# recipes

recipes is a simple to-the-point recipe database, slightly optimized for tablet usage.

## Set up

Clone the repository:
 
    $ git clone git://github.com/tueabra/recipes.git

Install the required packages (if needed):

    $ pip install -r requirements.txt

Create the database needed:

    $ cd recipes/recipes/
    $ python -c "from server import db; db.create_all();"

Run the recipe server:

    $ python server.py

Now recipes should be running on http://localhost:5000/. Hosting via apache or nginx is recommended.
