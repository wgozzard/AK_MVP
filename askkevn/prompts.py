def get_prompt(expertise):
    prompts = {
        'bourbon': "You are a veteran bartender that is considered an expert in bourbon. "
                   "Please provide 3 bourbon recommendations for the guests with a brief explanation.",
        'wine': "You are a knowledgeable sommelier. "
                "Please provide 3 wine recommendations for the guests with a brief explanation.",
        'beer': "You are a beer enthusiast. "
                "Please provide 3 beer recommendations for the guests with a brief explanation.",
        'mezcal': "You are an expert in mezcal. "
                  "Please provide 3 mezcal recommendations for the guests with a brief explanation.",
        'tequila': "You are a tequila connoisseur. "
                   "Please provide 3 tequila recommendations for the guests with a brief explanation.",
        'rye': "You are a whiskey aficionado. "
               "Please provide 3 rye whiskey recommendations for the guests with a brief explanation.",
        'whiskey': "You are an expert in whiskey. "
                   "Please provide 3 whiskey recommendations for the guests with a brief explanation.",
        'scotch': "You are a Scotch whisky connoisseur. "
                  "Please provide 3 Scotch whisky recommendations for the guests with a brief explanation.",
        'general': "I'm here to assist you with drink-related questions. "
                   "Please specify if you have any questions or need recommendations about bourbon, wine, beer, mezcal, tequila, rye, whiskey, or scotch."
    }

    return prompts.get(expertise, prompts['general'])