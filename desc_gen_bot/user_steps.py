class Steps:
    def __init__(self, address="", image="",
                 flat_description="", 
                 options="", deal_details = "",
                 current_step = 0,
                 infra_summary = None,
                 ):
        self._address = address
        self._image = image
        self._flat_description = flat_description
        self._options = options
        self._deal_details = deal_details
        self._current_step = current_step

        self._infra_summary = infra_summary


    def get(self):
        return {
            self._address,
            self._image,
            self._flat_description,
            self._options,
            self._deal_details,
            self._current_step,

            self._infra_summary
        }


class UserSteps:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        self._user_steps = {}

    def get_current_user_step(self, user_id):
        return self._user_steps.get(user_id)._current_step if self._user_steps.get(user_id) is not None else 0

    def get_current_user_data(self, user_id):
        return self._user_steps.get(user_id) if self._user_steps.get(user_id) is not None else {}


    def update_user_data(self, user_id, address = None, image = None,
                         flat_description = None, options = None, deal_details = None,
                         infra_summary = None,
                         ):
        user_data = self._user_steps.get(user_id)
        if user_data is None:
            user_data = Steps()

        if address != None:
            user_data._address = address
        if image != None:
            user_data._image = image
        if flat_description != None:
            user_data._flat_description = flat_description
        if options != None:
            user_data._options = options
        if deal_details != None:
            user_data._deal_details = deal_details
        if infra_summary != None:
            user_data._infra_summary = infra_summary

        self._user_steps[user_id] = user_data

    def increment_user_step(self, user_id):
        if self._user_steps[user_id]._current_step is None:
            self._user_steps[user_id]._current_step = 1
        else:
            self._user_steps[user_id]._current_step += 1

        if self._user_steps[user_id]._current_step > 4:
            self._user_steps[user_id]._current_step = 0