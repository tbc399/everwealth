from lucette import Lucette

from everwealth.budgets.events import sub

# from everwealth.auth.models.users import publisher

lucy = Lucette()

lucy.add_subscriber(sub)
