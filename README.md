# Commerce Website Back end

This is the back end of the E-commerce website I made. This is a personal project that I made for my own fun and learning.

The project is hosted on Vercel at https://commerce-site-backend.vercel.app/.

The front end is in a separate repository hosted on a separate domain. It is deployed at https://commerce-site-frontend.vercel.app/, and its source code can be found at https://github.com/benjaminJohnson2204/commerce-site-frontend.

## Tech Stack

I created the back end for the project using Django, Django Rest Framework, Django Rest Knox, and DRF Spectacular. 

For the database, I used a PostgreSQL database hosted on ElephantSQL.

## Scripts

To install the project's dependencies, run `pip install -r requirements.txt`.

To apply database migrations, run `python manage.py migrate`.

To run the server, run `python manage.py runserver`.

To run the tests, run `python manage.py test`.

## Code Structure

This project is a standard Django project named `server` and a single app named `rugs_app`. 

The database models are in `rugs_app/models.py`. The model serializers are in `rugs_app/serializer.py`. The views are in `rugs_app/views.py`.

## Database Models

I defined three database models for the project: Rug, User, and Order.
- **Rug**: A rug that can be bought on the site. Includes fields for a title, description, price, URL of an image of the rug, status (whether it's available to purchase), and when the rug was posted.
- **User**: A user of the website; inherits the functionality of Django's built-in authentication system. I customized this model with three additional fields: a list of rugs in the user's cart, and the user's preferences for receiving emails about their orders and about new rugs.
- **Order**: An order of rugs that a user has placed. Includes fields for which user placed the order, what rug(s) were ordered, the count of rugs in the order, the total price, the status (whether it's ready to pick up and whether it has been picked up), and when the order was placed, became ready, and was picked up.

## Serializers

Serializers are how models are converted into JSON to be sent in HTTP Responses. I used Django Rest Framework's default model serializers for my three models, and added a custom serializer for registering new users.

## API Routes

All API Routes and their documentation can be found at https://commerce-site-backend.vercel.app/api/docs.

Most of the routes fall in to one of four categories:
1. Authentication: Routes to register a new user, login, logout, verify a user's password, and get information about the user
2. Rugs: CRUD functionality for rugs 
3. Orders: CRUD functionatity for orders
4. Cart: Add to, remove from, and view a user's cart

## Tech Usage

In addition to using Django as the project's overarching framework, I used the following libraries for the following purposes:
- **Django Rest Framework**: DRF is a framework built upon Django that makes it easier to write REST APIs. I used DRF for generic API Views, permissions, and serialization.
- **Django Rest Knox**: Knox is a third-party plugin for Token Authentication in DRF. I used Knox instead of DRF's Token Authentication because Knox provides greater security with encrypted tokens and token expiration.
- **DRF Spectacular**: DRF Spectacular is a tool for documenting DRF APIs using OpenAPI and SwaggerUI. I used DRF Spectacular to annotate my APIs, generate an OpenAPI spec, and host a SwaggerUI for the API.

## Tests

I wrote tests for my API using Django's testing library, which is built upon Python's `unittest` library. 

Django's testing library automatically provides a test database and functionality to interface with the database and your Django server's routes.

The tests can be found in the `rugs_app/tests` directory. I divided my tests into three files:
- `test_auth`: Tests for the token authentication system, including registering, logging in, and logging out.
- `test_rugs`: Tests for the logic and permissions of creating, reading, updating, and deleting rugs.
- `test_orders`: Tests for the logic and permissions of adding rugs to a user's cart and removing from the cart, and creating, reading, updating, and deleting orders.