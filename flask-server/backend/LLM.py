import ollama
import ast
import re
import sys
import time

start_time = time.time()

default_model = 'dolphin-llama3'
STEPS = 0
PROGRESS = 0

# Function to extract recipe content from XML-like or formatted content
def extract_recipe(xml_content, pattern):
    match = re.search(pattern, xml_content, re.DOTALL)
    if not match:
        return None
    found_str = match.group(1)
    found_result = re.sub(r'\s+', ' ', found_str).strip()
    return found_result

# Function to parse a list of recipes from content
def parse_recipe_list(xml_content):
    try:
        dict_strs = extract_recipe(xml_content, r'<final_output>([\s\S]*?)</final_output>')
        recipe_list = []
        for dict_single in ast.literal_eval(dict_strs):
            recipe_list.append(dict_single)
    except:
        try:
            dict_strs = extract_recipe(xml_content, r'```python([\s\S]*?)```')
            recipe_list = []
            for dict_single in ast.literal_eval(dict_strs):
                recipe_list.append(dict_single)
        except:
            try:
                dict_strs = extract_recipe(xml_content, r'```([\s\S]*?)```')
                recipe_list = []
                for dict_single in ast.literal_eval(dict_strs):
                    recipe_list.append(dict_single)
            except:
                try:
                    dict_strs = '[' + extract_recipe(xml_content, r'\[(.*?)\]') + ']'
                    recipe_list = []
                    for dict_single in ast.literal_eval(dict_strs):
                        recipe_list.append(dict_single)
                except:
                    return None
    return recipe_list

# Optional: Convert the extracted content into an actual dictionary
def parse_recipe_dict(xml_content):
    dict_str = extract_recipe(xml_content, r'<final_output>\s*({[\s\S]*?})\s*</final_output>')
    if dict_str:
        try:
            return eval(dict_str)  # Caution: Use eval() only with trusted input
        except:
            return None
    return None

# Function to create a recipe dictionary
def write_recipe(name: str, description: str, ingredients: list[str]=None, cost: int=0, cuisine: str=None, serving_size: int=0, meal_type: str=None,
                 allergies=None, diet: str=None) -> dict[str, str]:
    if allergies is None:
        allergies = ['None']

    with open('system_prompt', 'r') as f:
        system_prompt = {'role': 'system', 'content': str(f.read())}

    user_prompt = {'role': 'user', 'content': f"Recipe Name: {name}; "
                                              f"Description: {description}; "
                                              f"{'Requested Ingredients: ' + ', '.join(ingredients) if ingredients else 'No specific ingredient provided'}; "
                                              f"{'Cost $: ' + str(cost) + '; ' if cost > 0 else ''}"
                                              f"{'Cuisine type: ' + cuisine + '; ' if cuisine else ''}"
                                              f"{'Serving size: ' + str(serving_size) + '; ' if serving_size > 0 else ''}"
                                              f"{'Meal type: ' + meal_type + '; ' if meal_type else ''}"
                                              f"{'Allergies: ' + ', '.join(allergies) + '; ' if allergies else ''}"
                                              f"{'Diet: ' + diet + '; ' if diet else ''}"}

    count = 0
    while count < 10:
        count += 1
        global STEPS
        STEPS += 1
        response = ollama.chat(
            model=default_model,
            messages=[system_prompt, user_prompt],
        )['message']['content']

        try:
            recipe_dict = parse_recipe_dict(response)
            assert type(recipe_dict) == dict
            assert type(recipe_dict['ingredients']) is list
            assert type(recipe_dict['instructions']) is list
            return recipe_dict
        except Exception as e:
            pass

    return False

# Function to create a list of recipes
def create_recipe_list(ingredients: list[str]=None, cost: int=0, cuisine: str=None, serving_size: int=0, meal_type: str=None,
                       allergies=None, diet: str=None) -> list[dict[str, str]]:
    if allergies is None:
        allergies = ['None']

    with open('system_prompt2', 'r') as f:
        system_prompt = {'role': 'system', 'content': str(f.read())}

    # Capture ingredients passed from Flask as a list of strings
    user_prompt = {'role': 'user', 'content': f"The ingredients are: {', '.join(ingredients)}; "
                                              f"{'Cost $: ' + str(cost) + '; ' if cost > 0 else ''}"
                                              f"{'Cuisine type: ' + cuisine + '; ' if cuisine else ''}"
                                              f"{'Serving size: ' + str(serving_size) + '; ' if serving_size > 0 else ''}"
                                              f"{'Meal type: ' + meal_type + '; ' if meal_type else ''}"
                                              f"{'Allergies: ' + ', '.join(allergies) + '; ' if allergies else ''}"
                                              f"{'Diet: ' + diet + '; ' if diet else ''}"}

    count = 0
    while count < 10:
        count += 1
        global STEPS
        STEPS += 1

        response = ollama.chat(
            model=default_model,
            messages=[system_prompt, user_prompt],
        )['message']['content']

        try:
            recipe_list_dict = parse_recipe_list(response)
            assert type(recipe_list_dict) is list
            assert type(recipe_list_dict[0]) is dict
            assert type(recipe_list_dict[0]['recipe']) is str
            assert type(recipe_list_dict[0]['description']) is str

            return recipe_list_dict
        except Exception as e:
            pass

    return []

if __name__ == "__main__":
    ingredients = sys.argv[1:] if len(sys.argv) > 1 else []

    recipes_list = create_recipe_list(ingredients=ingredients)
    
    recipes = []
    for recipe in recipes_list:
        recipes.append(write_recipe(*recipe.values()))

    for index, recipe in enumerate(recipes):
        recipe_name = recipes_list[index]['recipe']
        recipe_description = recipes_list[index]['description']
        recipe_ingredients = recipe['ingredients']
        recipe_instructions = recipe['instructions']

        formatted_recipe = f"""
        <div class="recipe-container">
            <div class="recipe-header" onclick="toggleRecipeDetails('recipe-{index+1}')">
                <h3>Recipe {index + 1}: {recipe_name}</h3>
            </div>
            <div class="recipe-content" id="recipe-{index+1}">
                <p><strong>Description:</strong> {recipe_description}</p>
                <p><strong>Ingredients:</strong></p>
                <ul>
                    {"".join([f"<li>{ingredient}</li>" for ingredient in recipe_ingredients])}
                </ul>
                <p><strong>Instructions:</strong></p>
                <ol>
                    {"".join([f"<li>{instruction}</li>" for instruction in recipe_instructions])}
                </ol>
            </div>
        </div>
        """
        print(formatted_recipe)