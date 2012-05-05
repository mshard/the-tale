# coding: utf-8

from ...actions.prototypes import ActionMoveToPrototype

from ..prototypes import AbilityPrototype

attrs = None

class ShortTeleport(AbilityPrototype):

    LIMITED = False
    INITIAL_LIMIT = None

    COST = 3
    COOLDOWN = 15

    NAME = u'Подтолкнуть'
    DESCRIPTION = u'Телепортировать героя на короткое расстояние'
    ARTISTIC = u'Маленький толчок, и ваш подопечный уже влетает в дереве в нескольких километрах впереди.'

    FORM = None
    TEMPLATE = None

    def use(self, bundle, angel, hero, form):
        move_action = bundle.current_hero_action(hero.id)

        if move_action.type != ActionMoveToPrototype.TYPE:
            return False

        if not move_action.short_teleport(3):
            return False

        hero.add_message('angel_ability_shortteleport', hero=hero)

        return True
