import logging
from evanlu.intent import IntentRecognizer
from evanlu.filter import NonSenseFilter, SensitiveFilter
from evanlu.entity import EntityRecognizer
from evanlu.io import IO, NLUFileIO

log = logging.getLogger(__name__)


class NLURobot(object):
    robots = {}

    """
    
    Attributes
    ----------
    _io : NLUFileIO
    
    """
    def __init__(self, io: NLUFileIO):
        self.domain_id = io.domain_id
        log.info("CREATE NLU ROBOT: {0}".format(io.domain_id))
        self._nonsense = None
        self._sensitive = None
        self._entity = None
        self._intent = None
        self._filtered_intents = ["casual_talk", "sensitive", "nonsense"]
        self._entities_by_intent = {
            "casual_talk": [],
            "sensitive": [],
            "nonsense": [],
        }
        self._io = io

    def init(self):
        self._nonsense = NonSenseFilter.get_filter(self._io)
        self._sensitive = SensitiveFilter.get_filter(self._io)
        self._entity = EntityRecognizer.get_entity_recognizer(self._io)
        self._intent = IntentRecognizer.get_intent_recognizer(self._io)
        self._entities_by_intent = self._io.get_all_intent_entities()

    @classmethod
    def get_robot(cls, domain_id):
        robot = cls.robots.get(domain_id, None)
        if robot:
            return robot
        robot = NLURobot(IO(domain_id))
        robot.init()
        cls.robots[domain_id] = robot
        return robot

    @classmethod
    def reset_robot(cls, domain_id):
        robot = NLURobot(IO(domain_id))
        robot.init()
        cls.robots[domain_id] = robot
        return robot

    def train(self):
        """ Fetch labeld data of project from database,
        and train with questions

        Returns
        -------
        {
            "intents": [

                "label": 意图标识,

                "count": 问题数量,

                "precise": 准去率,

            ]

            "total_prciese": 业务准确率

        }
        """
        label_data = self._io.get_label_data()
        if not label_data:
            return {
                "intents": []
            }
        ret = self._intent.train(label_data)
        return ret

    def predict(self, context, question):
        """ Return NLU result such as intent and entities.

        Parameters
        ----------
        context : dict
            Context info from DM.
        question : str
            Dialogue text.

        Returns
        -------
        dict.

        """
        log.info("----------------%s------------------" % question)

        # when context given, detect entities
        if context["intent"] is not None:
            intent = context["intent"]
            if intent in self._filtered_intents:
                entities = []
            else:
                entities = self._entities_by_intent[intent]
            d_entities = self._entity.recognize(question, entities)
            if d_entities:
                return {
                    "question": question,
                    "intent": intent,
                    "confidence": 1.0,
                    "entities": d_entities,
                    "related_entities": entities,
                    "node_id": None
                }
        priority = context["agents"]
        # detect intent and entities
        s_intent, confidence, node_id = self._intent_classify(priority,
                                                              question)
        slot_values = {}
        target_slots = None
        intent2entities = self._io.get_all_intent_entities()
        if s_intent and s_intent not in self._filtered_intents:
            slots = intent2entities[s_intent]["slots"]
            target_slots = list(slots.keys())
            d_entities = self._entity.recognize(question,
                                                set(slots.values()))
            log.debug("ENTITIES DETECT to {0}".format(d_entities))
            # @BUG from_city to_city
            slots = {v: k for k, v in slots.items()}
            for entity, value in d_entities.items():
                slot_values[slots[entity]] = value

        return {
            "question": question,
            "intent": "casual_talk" if s_intent is None else s_intent,
            "confidence": confidence,
            "entities": slot_values,
            "target_entities": target_slots,
            "node_id": node_id
        }

    def _intent_classify(self, context, question):
        log.debug("Sensitive detecting.")
        if self._sensitive.detect(question):
            log.info("FILTERED QUESTION")
            return "sensitive", 1.0, None

        intent, confidence, node_id = self._intent.strict_classify(
            context, question)
        if intent:
            return intent, confidence, node_id

        intent, confidence, node_id = self._intent.rule_classify(
            context, question)
        if intent:
            return intent, confidence, node_id

        if self._nonsense.detect(question):
            log.info("NONSENSE QUESTION")
            return "nonsense", 1.0, None

        return "casual_talk", 1.0, None

        # intent, confidence, node_id = self._intent.fuzzy_classify(
        #     context, question)
        # log.info("FUZZY CLASSIFY to {0} confidence {1}".format(
        #     intent, confidence))
        # return intent, confidence, node_id
