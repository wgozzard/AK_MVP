from .imports import *

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(request, username=username, password=password)
            login(request, user)
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # Handle login form submission
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                # Set session variable to indicate prompt has been displayed
                session_key = request.session.session_key
                if session_key:
                    session = Session.objects.get(session_key=session_key)
                    session['prompt_displayed'] = True
                    session.save()

                return redirect('home')  # Redirect to the home page after successful login
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form})
@login_required
def chatbot(request):
    chatbot_response = None
    api_key = os.environ.get("OPENAI_KEY")
    user_input = ''

    if api_key is not None and request.method == 'POST':
        openai.api_key = api_key
        user_input = request.POST.get('user_input')

        if user_input:
            expertise = determine_expertise(user_input)

            prompt = get_prompt(expertise)

            # Check if the expertise area requires inventory-based recommendations
            if expertise in ['bourbon', 'whiskey', 'wine', 'beer', 'mezcal', 'tequila', 'rye', 'scotch']:
                inventory_items = cache.get('inventory_items')  # Try to retrieve inventory data from cache

                if inventory_items is None:
                    # Data not found in cache, fetch from the database
                    inventory_items = get_inventory_items()
                    cache.set('inventory_items', inventory_items)  # Store the data in cache

                inventory_prompt = generate_inventory_prompt(inventory_items)
                prompt += '\n\n' + inventory_prompt

            if 'clear_button' in request.POST:
                # Clear the prompt and question if the clear button is clicked
                user_input = ''
            else:
                # Include the user's question in the prompt
                prompt += "\n\n" + user_input

            try:
                response = openai.Completion.create(
                    engine='text-davinci-003',
                    prompt=prompt,
                    max_tokens=175,
                    temperature=0.2,
                )

                if response and response["choices"]:
                    chatbot_response = response["choices"][0]['text']

                    # Clean up the response by removing leading punctuation marks
                    chatbot_response = chatbot_response.lstrip(string.punctuation).strip()

                    # Remind the server if the question is not related to alcohol
                    if expertise == 'general' and 'alcohol' not in chatbot_response:
                        chatbot_response += "\n\nPlease remember that I'm here to assist you with drink-related questions."

                    # Check if the chatbot response contains an inventory match
                    if "*Inventory Match:" not in chatbot_response:
                        # Reset the cache or clear inventory items from memory
                        cache.delete('inventory_items')

            except Exception as e:
                # Handle the exception appropriately
                pass

    return render(request, 'main.html', {'response': chatbot_response, 'user_input': user_input})



def get_inventory_items():
    try:
        json_file_path = os.path.join(BASE_DIR, 'media', 'inventory.json')

        with open(json_file_path, 'r') as file:
            inventory_data = json.load(file)
            inventory_items = []

            for item_data in inventory_data:
                item = {
                    'alcohol_type': item_data['Alcohol Type'],
                    'brand': item_data['Brand'],
                    'price': item_data['Price']
                }
                inventory_items.append(item)

        return inventory_items
    except FileNotFoundError:
        return []

def generate_inventory_prompt(inventory_items):
    inventory_prompt = ""
    for item in inventory_items:
        if isinstance(item, dict):
            inventory_prompt += f"{item['alcohol_type']} - {item['brand']}\n"
        elif isinstance(item, InventoryItem):
            inventory_prompt += f"{item.alcohol_type} - {item.brand}\n"
    return inventory_prompt

def is_bar_manager(user):
    return user.groups.filter(name='Bar Manager').exists()

def permission_denied(request):
    return render(request, '403.html', status=403)

@user_passes_test(is_bar_manager, login_url='403')
@login_required
def upload_inventory(request):
    if request.method == 'POST':
        form = InventoryUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Clear existing inventory items
            InventoryItem.objects.filter(owner=request.user).delete()

            # Clear inventory items from cache
            cache.delete('inventory_items')

            # Process the inventory file using pandas
            try:
                inventory_file = request.FILES['inventory_file']

                # Convert Excel file to JSON
                data = pd.read_excel(inventory_file)
                json_data = data.to_json(orient='records')

                # Save JSON data to a temporary file
                temp_file_path = os.path.join(BASE_DIR, 'temp', 'inventory.json')
                with open(temp_file_path, 'w') as file:
                    file.write(json_data)

                # Move the temporary file to the desired location
                # (e.g., a media directory accessible by the web app)
                target_file_path = os.path.join(BASE_DIR, 'media', 'inventory.json')
                shutil.move(temp_file_path, target_file_path)

                return redirect('upload_preview')  # Redirect to the upload_preview page
            except Exception as e:
                error_message = f"Error processing the inventory file: {str(e)}"
                return render(request, 'upload_inventory.html', {'form': form, 'error_message': error_message})
        else:
            # Form is not valid
            pass
    else:
        form = InventoryUploadForm()

    return render(request, 'upload_inventory.html', {'form': form})


@login_required
def delete_file(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')  # Retrieve the file_id from the form
        inventory_item = get_object_or_404(InventoryItem, id=file_id)
        inventory_item.delete()
        return redirect('upload_preview')
    else:
        # Handle GET request if needed
        return redirect('upload_preview')

@login_required
def save_inventory(request):
    if request.method == 'POST':
        inventory_items = request.POST.getlist('inventory_item')

        # Process the inventory items and save them to the database
        for item in inventory_items:
            item_data = item.split(',')
            inventory_item = InventoryItem(
                owner=request.user,
                alcohol_type=item_data[0],
                brand=item_data[1],
                price=float(item_data[2])
            )
            inventory_item.save()

        return redirect('home')  # Redirect to the desired page after saving the inventory

    return redirect('upload_preview')  # Redirect back to the upload preview page if the request method is not POST

@login_required
def upload_preview(request):

    inventory_items = cache.get('inventory_items', default=None)  # Try to retrieve inventory data from cache

    if inventory_items is None:
        # Data not found in cache, read and parse the JSON file
        json_file_path = os.path.join(BASE_DIR, 'media', 'inventory.json')

        try:
            with open(json_file_path, 'r') as file:
                inventory_data = json.load(file)
                inventory_items = []

                for item_data in inventory_data:
                    item = InventoryItem(
                        alcohol_type=item_data['Alcohol Type'],
                        brand=item_data['Brand'],
                        price=item_data['Price']
                    )
                    inventory_items.append(item)

            cache.set('inventory_items', inventory_items)  # Store the data in cache
        except FileNotFoundError:
            inventory_items = []

    # Pass the inventory_items to the template for rendering

    return render(request, 'upload_preview.html', {'inventory_items': inventory_items})

@login_required
def clear_inventory(request):
    if request.method == 'POST':
        # Clear the existing inventory items associated with the user
        InventoryItem.objects.filter(owner=request.user).delete()

        # Clear inventory items from cache
        cache.delete('inventory_items')

        # Redirect to the appropriate page after clearing the inventory
        return redirect('upload_preview')

    return redirect('upload_inventory')
