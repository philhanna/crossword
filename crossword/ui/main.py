from crossword.ui import create_app

from crossword.ui.uimain import uimain
from crossword.ui.uigrid import uigrid
from crossword.ui.uipuzzle import uipuzzle
from crossword.ui.uipublish import uipublish
from crossword.ui.uiword import uiword
from crossword.ui.uiwordlists import uiwordlists

app = create_app()

app.register_blueprint(uimain)
app.register_blueprint(uigrid)
app.register_blueprint(uipuzzle)
app.register_blueprint(uipublish)
app.register_blueprint(uiword)
app.register_blueprint(uiwordlists)

app.run()
