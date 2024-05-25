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

def is_bar_manager(user):
    return user.groups.filter(name='Bar Manager').exists()

def permission_denied(request):
    return render(request, '403.html', status=403)

@login_required
@user_passes_test(is_bar_manager, login_url='403')
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
                inventory_data = data.to_dict('records')

                # Save inventory data as a dictionary
                inventory_items = []
                for item_data in inventory_data:
                    item = {
                        'alcohol_type': item_data['Alcohol Type'],
                        'brand': item_data['Brand'],
                        'price': item_data['Price']
                    }
                    inventory_items.append(item)

                # Store the inventory dictionary in cache
                cache.set('inventory_items', inventory_items)

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
def upload_preview(request):
    if is_bar_manager(request.user) or request.user.is_authenticated:
        inventory_items = cache.get('inventory_items', default=None)  # Try to retrieve inventory data from cache

        if inventory_items is None:
            # Data not found in cache, read and parse the JSON file
            inventory_items = get_inventory_items()
            cache.set('inventory_items', inventory_items)  # Store the data in cache
    else:
        inventory_items = []

    return render(request, 'upload_preview.html', {'inventory_items': inventory_items})

@login_required
def chatbot(request):
    chatbot_response = None
    user_input = request.POST.get('user_input', '')
    api_key = os.environ.get("OPENAI_KEY")  # Retrieve the API key from environment variable

    if user_input:
        expertise = determine_expertise(user_input)
        prompt = get_prompt(expertise)

        if expertise == 'price':
            alcohol = extract_alcohol_from_input(user_input)  # Implement a function to extract the alcohol name from the user input
            prompt = get_prompt(expertise, alcohol)

        if expertise in ['bourbon', 'whiskey', 'wine', 'beer', 'mezcal', 'tequila', 'rye', 'scotch']:
            inventory_items = cache.get('inventory_items')

            if inventory_items is None:
                inventory_items = get_inventory_items()
                cache.set('inventory_items', inventory_items)

            filtered_items = filter_inventory_items(inventory_items, expertise)
            inventory_prompt = generate_inventory_prompt(filtered_items, expertise)
            prompt += '\n\n' + inventory_prompt

        if 'clear_button' in request.POST:
            user_input = ''
        else:
            prompt += "\n\n" + user_input

        try:
            response = openai.ChatCompletion.create(
                model='gpt-4',
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=175,
                temperature=0.2,
                api_key=api_key  # Pass the API key to authenticate the request
            )

            if response and response["choices"]:
                chatbot_response = response["choices"][0]["message"]["content"]
                chatbot_response = chatbot_response.lstrip(string.punctuation).strip()

                if expertise == 'general' and 'alcohol' not in chatbot_response:
                    chatbot_response += "\n\nPlease remember that I'm here to assist you with drink-related questions."

                if "*Inventory Match:" not in chatbot_response:
                    cache.delete('inventory_items')

        except Exception as e:
            # Handle the exception appropriately
            pass

    return render(request, 'main.html', {'response': chatbot_response, 'user_input': user_input})
   
def extract_alcohol_from_input(user_input):
    # Regular expression pattern to extract alcohol name between quotes or after "price of"
    pattern = r'"([^"]+)"|price of\s+(\w+)'

    match = re.search(pattern, user_input, re.IGNORECASE)
    if match:
        alcohol_name = match.group(1) or match.group(2)
        return alcohol_name.strip()

    return None
    
def get_inventory_items():
    try:
        inventory_items = cache.get('inventory_items')
        if inventory_items is not None:
            return inventory_items

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


def generate_inventory_prompt(inventory_items, alcohol_type):
    inventory_prompt = ""
    for item in inventory_items:
        if item['alcohol_type'].lower() == alcohol_type.lower():
            inventory_prompt += f"{item['brand']} - {item['price']}\n"
    return inventory_prompt

def filter_inventory_items(inventory_items, alcohol_type):
    filtered_items = []
    for item in inventory_items:
        if item['alcohol_type'].lower() == alcohol_type.lower():
            filtered_items.append(item)
    return filtered_items

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

        return redirect('home')  # Redirect to the upload_preview page after saving the inventory

    return redirect('upload_preview')  # Redirect back to the upload_preview page if the request method is not POST

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
