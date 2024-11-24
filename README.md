# Project 2402: La casa del Sol Webpage
## La casa del Sol Webpage Development Repository
## Inspiration

This webpage is built on top of [this BS5 template](https://themewagon.com/themes/free-bootstrap-5-html5-website-template-klar/).

## Environment

- Python 3.10.12
- Ubuntu 22.04 LTS

### Setup

1. Create a python virtual environment ```python3 -m venv venv```
2. Switch to the virtual environment

```sh
source venv/bin/activate # Linux
```

```ps
venv/bin/Activate.ps1 # Windows
```



3. Install all dependencies by running ```pip install -r requirements.txt```

Once the above steps are completed you will be able to run the development server by just typing the following command in:

```sh
flask --app app run --debug
```

### Multilingual Support

This webpage supports both **English and Spanish** languages. 
As the default language is English, there is no need to specify the language in the URL.

- To switch to Spanish, just add ```/es``` to the URL. For example, to switch to Spanish on the home page, you would navigate to ```https://
www.will-soft.net/es```.

- If the ```/en``` or ```/es``` is not present in the URL, the webpage will default to English.

The language is stored as a global variable in the session object. Some default Flask functions have been overridden to support this feature, such as the ```url_for``` function, that now includes the language in the URL (we have named it ```url_for_lang```).

Most of the jinja templates have been updated to support this feature. The language is stored in the session object, and the templates are updated to display the correct language based on the session object, if you find any template that is not updated, please let me know so I can update it (or you can do it yourself ;)).

