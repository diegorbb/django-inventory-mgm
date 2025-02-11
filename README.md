## Generate a key

You can use https://djecrety.ir/ to generate a key for the project.

Once you have a key, follow these steps:
- Create an .env in the root directory
- Add a variable of SECRET_KEY with the newly generated key
- Save the changes

## Install requirements

Change the directory to the same dir requirements.txt is and run: `pip install -r requirements.txt`

## Create a superuser

To create a superuser, change directory to inventory and run: `python3 manage.py createsuperuser` and follow the prompts.

## Run the project

Once you have all the libraries installed and a superuser, cd into `inventory` and run `python3 manage.py runserver`
