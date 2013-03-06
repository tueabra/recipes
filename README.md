# recipes

recipes is a simple to-the-point recipe database, slightly optimized for tablet usage.

Please note that is a very simple project, written for personal use only.

All the text is currently in danish.

## Set up

Clone the repository:
 
    $ git clone git://github.com/tueabra/recipes.git

Install the required packages (if needed):

    $ pip install -r requirements.txt

Create the database needed:

    $ cd recipes/recipes/
    $ python server.py initdb

Run the recipe server:

    $ python server.py runserver

Now recipes should be running on http://localhost:5000/. Hosting via apache or nginx is recommended.
