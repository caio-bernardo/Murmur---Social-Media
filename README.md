# Murmur - A Social Media Showcase Project

Do you hear _murmurs_ about a new social media on the rise (probably not)!
This is **Murmur**, a _fake_ social media application, build to learn and have some fun. Just like other apps, you can create your account and post things you think are worth sharing on the internet! You can also like - or deslike - posts and make comments.

## Features
- [x] Create an account
- [x] Make posts, comment and react to other peoples posts!
- [ ] Nice feed of people's posts
- [ ] COMMING SOON! Beautiful front-end! Using [Pico CSS](https://picocss.com/) and [Alpine.js](https://alpinejs.dev/), there is this nice wepapp you can play with.
- [x] RESTful API. We provide an API with user auth, posts, comments and reactions endpoints. Check the docs for more info!
- [x] API documentation, powered by OpenAPI.
- [ ] Authenticate with Google, Github and others...

## Availability

Currently the project ** is not** available on-line, but there are plans for deployment comming soon! Stay tuned...

## Technologies

This project is entirely built with Django. For the API I used:
+ [Django Ninja](https://django-ninja.dev/) for the routes and schemas
+ Postgres for the database
+ Docker for containarization, deployment and development
+ Pytest for testing and debugging
For the frontend:
+ [Django-cotton](https://django-cotton.com/) for components
+ [Pico CSS](https://picocss.com/) for styling
+ [Alpine.js](https://alpinejs.dev/) for interactivity

## Contributing

If you have ideas to improve the project, let's discuss on the Issues page. If you want to make a Pull Request or just toy around, here are the steps to make this run locally.

1. Clone the project
2. Have [Docker and Docker Compose](https://www.docker.com/) installed
3. Setup the enviroment variables following `.env.example`
4. Spin up the application in development mode: `docker compose up --watch`. And there you have it!
