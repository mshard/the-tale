# coding: utf-8
import mock
import random

from textgen.words import Noun

from common.utils import testcase

from accounts.logic import register_user

from game.balance.enums import RACE

from game.prototypes import TimePrototype
from game.logic import create_test_map
from game.heroes.prototypes import HeroPrototype
from game.balance import constants as c

from game.map.conf import map_settings

from game.map.places.models import Building
from game.map.places.prototypes import BuildingPrototype, ResourceExchangePrototype
from game.map.places.storage import places_storage, buildings_storage
from game.map.places.relations import RESOURCE_EXCHANGE_TYPE
from game.map.places import modifiers


class PlacePrototypeTests(testcase.TestCase):

    def setUp(self):
        super(PlacePrototypeTests, self).setUp()
        self.p1, self.p2, self.p3 = create_test_map()

        result, account_id, bundle_id = register_user('test_user1', 'test_user1@test.com', '111111')
        self.hero_1 = HeroPrototype.get_by_account_id(account_id)

        result, account_id, bundle_id = register_user('test_user2', 'test_user2@test.com', '111111')
        self.hero_2 = HeroPrototype.get_by_account_id(account_id)

        result, account_id, bundle_id = register_user('test_user3', 'test_user3@test.com', '111111')
        self.hero_3 = HeroPrototype.get_by_account_id(account_id)

        current_time = TimePrototype.get_current_time()
        current_time.increment_turn()


    def test_initialize(self):
        self.assertEqual(self.p1.heroes_number, 0)

    def test_sync_race_no_signal_when_race_not_changed(self):
        with mock.patch('game.map.places.signals.place_race_changed.send') as signal_counter:
            self.p1.sync_race()

        self.assertEqual(signal_counter.call_count, 0)

    def test_sync_race_signal_when_race_changed(self):
        for race in RACE._ALL:
            if self.p1.race != race:
                self.p1.race = race
                self.p1.save()
                break

        with mock.patch('game.map.places.signals.place_race_changed.send') as signal_counter:
            self.p1.sync_race()

        self.assertEqual(signal_counter.call_count, 1)

    def test_sync_size__good_changing(self):
        self.p1.production = 10

        self.assertEqual(self.p1.goods, 0)
        self.p1.sync_size(2)
        self.assertEqual(self.p1.goods, 20)

        self.p1.production = -10
        self.p1.goods = 11
        self.p1.sync_size(1)
        self.assertEqual(self.p1.goods, 1)

    def test_sync_size__size_increased(self):
        self.p1.production = 10

        self.p1.goods = c.PLACE_GOODS_TO_LEVEL
        self.p1.size = 1
        self.p1.sync_size(1)
        self.assertEqual(self.p1.goods, c.PLACE_GOODS_TO_LEVEL * c.PLACE_GOODS_AFTER_LEVEL_UP)
        self.assertEqual(self.p1.size, 2)

        self.p1.goods = c.PLACE_GOODS_TO_LEVEL
        self.p1.size = 10
        self.p1.sync_size(1)
        self.assertEqual(self.p1.goods, c.PLACE_GOODS_TO_LEVEL)
        self.assertEqual(self.p1.size, 10)

    def test_sync_size__size_decreased(self):
        self.p1.production = -10

        self.p1.goods = 0
        self.p1.size = 2
        self.p1.sync_size(1)
        self.assertEqual(self.p1.goods, c.PLACE_GOODS_TO_LEVEL * c.PLACE_GOODS_AFTER_LEVEL_DOWN)
        self.assertEqual(self.p1.size, 1)

        self.p1.goods = 0
        self.p1.size = 1
        self.p1.sync_size(1)
        self.assertEqual(self.p1.goods, 0)
        self.assertEqual(self.p1.size, 1)

    def _create_test_exchanges(self):
        ResourceExchangePrototype.create(place_1=self.p1,
                                         place_2=self.p2,
                                         resource_1=RESOURCE_EXCHANGE_TYPE.PRODUCTION_SMALL,
                                         resource_2=RESOURCE_EXCHANGE_TYPE.NONE,
                                         bill=None)

        ResourceExchangePrototype.create(place_1=self.p1,
                                         place_2=self.p3,
                                         resource_1=RESOURCE_EXCHANGE_TYPE.NONE,
                                         resource_2=RESOURCE_EXCHANGE_TYPE.PRODUCTION_LARGE,
                                         bill=None)

        ResourceExchangePrototype.create(place_1=self.p1,
                                         place_2=self.p2,
                                         resource_1=RESOURCE_EXCHANGE_TYPE.SAFETY_SMALL,
                                         resource_2=RESOURCE_EXCHANGE_TYPE.NONE,
                                         bill=None)

        ResourceExchangePrototype.create(place_1=self.p1,
                                         place_2=self.p3,
                                         resource_1=RESOURCE_EXCHANGE_TYPE.NONE,
                                         resource_2=RESOURCE_EXCHANGE_TYPE.SAFETY_LARGE,
                                         bill=None)

        ResourceExchangePrototype.create(place_1=self.p1,
                                         place_2=self.p2,
                                         resource_1=RESOURCE_EXCHANGE_TYPE.TRANSPORT_SMALL,
                                         resource_2=RESOURCE_EXCHANGE_TYPE.NONE,
                                         bill=None)

        ResourceExchangePrototype.create(place_1=self.p1,
                                         place_2=self.p3,
                                         resource_1=RESOURCE_EXCHANGE_TYPE.NONE,
                                         resource_2=RESOURCE_EXCHANGE_TYPE.TRANSPORT_LARGE,
                                         bill=None)


    @mock.patch('game.balance.formulas.place_goods_production', lambda size: 100 if size < 5 else 1000)
    @mock.patch('game.map.places.modifiers.prototypes.CraftCenter.PRODUCTION_MODIFIER', 10000)
    @mock.patch('game.persons.prototypes.PersonPrototype.production', 1)
    def test_sync_sync_parameters__production(self):
        self.p1.modifier = modifiers.CraftCenter.get_id()
        self.p1.size = 1
        self.p1.expected_size = 6

        self._create_test_exchanges()

        self.p1.sync_parameters()

        expected_production = 10900 + len(self.p1.persons) - RESOURCE_EXCHANGE_TYPE.PRODUCTION_SMALL.amount + RESOURCE_EXCHANGE_TYPE.PRODUCTION_LARGE.amount

        self.assertTrue(-0.001 < self.p1.production - expected_production < 0.001)

    @mock.patch('game.map.places.modifiers.prototypes.Fort.SAFETY_MODIFIER', 0.01)
    @mock.patch('game.persons.prototypes.PersonPrototype.safety', -0.001)
    def test_sync_sync_parameters__safety(self):
        self.p1.modifier = modifiers.Fort.get_id()

        self._create_test_exchanges()

        self.p1.sync_parameters()

        expected_safety = (1.0 - c.BATTLES_PER_TURN + 0.01 - 0.001 * len(self.p1.persons) -
                           RESOURCE_EXCHANGE_TYPE.SAFETY_SMALL.amount + RESOURCE_EXCHANGE_TYPE.SAFETY_LARGE.amount)

        self.assertTrue(-0.001 < self.p1.safety - expected_safety < 0.001)

    @mock.patch('game.map.places.modifiers.prototypes.TransportNode.TRANSPORT_MODIFIER', 0.01)
    @mock.patch('game.persons.prototypes.PersonPrototype.transport', 0.001)
    def test_sync_sync_parameters__transport(self):
        self.p1.modifier = modifiers.TransportNode.get_id()

        self._create_test_exchanges()

        self.p1.sync_parameters()

        expected_transport = (1.0 + 0.01 + 0.001 * len(self.p1.persons) -
                              RESOURCE_EXCHANGE_TYPE.TRANSPORT_SMALL.amount + RESOURCE_EXCHANGE_TYPE.TRANSPORT_LARGE.amount)

        self.assertTrue(-0.001 < self.p1.transport - expected_transport < 0.001)

    @mock.patch('game.map.places.modifiers.prototypes.Polic.FREEDOM_MODIFIER', 0.01)
    @mock.patch('game.persons.prototypes.PersonPrototype.freedom', 0.001)
    def test_sync_sync_parameters__freedom(self):
        self.p1.modifier = modifiers.Polic.get_id()

        self._create_test_exchanges()

        self.p1.sync_parameters()

        self.assertTrue(-0.001 < self.p1.freedom - (1.0 + 0.01 + 0.001 * len(self.p1.persons)) < 0.001)

    def test_get_experience_modifier(self):
        self.assertEqual(self.p1.get_experience_modifier(), 0.0)
        self.p1.modifier = modifiers.Polic.get_id()
        self.assertEqual(self.p1.get_experience_modifier(), 0.0)
        self.p1.modifier = modifiers.Outlaws.get_id()
        self.assertEqual(self.p1.get_experience_modifier(), 0.25)


class BuildingPrototypeTests(testcase.TestCase):

    def setUp(self):
        super(BuildingPrototypeTests, self).setUp()
        self.place_1, self.place_2, self.place_3 = create_test_map()


    def test_get_available_positions(self):

        building = BuildingPrototype.create(self.place_1.persons[0], name_forms=Noun.fast_construct('building-name'))

        positions = BuildingPrototype.get_available_positions(self.place_1.x, self.place_1.y)

        self.assertTrue(positions)

        for place in places_storage.all():
            self.assertFalse((place.x, place.y) in positions)

        for building in buildings_storage.all():
            self.assertFalse((building.x, building.y) in positions)

        for x, y in positions:
            self.assertTrue(0 <= x < map_settings.WIDTH)
            self.assertTrue(0 <= y < map_settings.HEIGHT)


    def test_dynamic_position_radius(self):
        with mock.patch('game.map.places.conf.places_settings.BUILDING_POSITION_RADIUS', 2):
            positions = BuildingPrototype.get_available_positions(-3, -1)
            self.assertEqual(positions, set([(0, 0), (0, 1), (0, 2)]))

        with mock.patch('game.map.places.conf.places_settings.BUILDING_POSITION_RADIUS', 2):
            positions = BuildingPrototype.get_available_positions(-4, -1)
            self.assertEqual(positions, set([(0, 0), (0, 1), (0, 2), (0, 3)]))

    def test_create(self):
        self.assertEqual(Building.objects.all().count(), 0)

        old_version = buildings_storage.version

        name = Noun.fast_construct('building-name')

        building = BuildingPrototype.create(self.place_1.persons[0], name_forms=name)

        self.assertNotEqual(old_version, buildings_storage.version)

        self.assertEqual(Building.objects.all().count(), 1)

        old_version = buildings_storage.version

        name_2 = Noun.fast_construct('building-name-2')
        building_2 = BuildingPrototype.create(self.place_1.persons[0], name_forms=name_2)

        self.assertEqual(old_version, buildings_storage.version)
        self.assertEqual(Building.objects.all().count(), 1)
        self.assertEqual(hash(building), hash(building_2))
        self.assertEqual(building.normalized_name, name)

    def test_create_after_destroy(self):
        self.assertEqual(Building.objects.all().count(), 0)

        old_version = buildings_storage.version

        person = self.place_1.persons[0]

        name = Noun.fast_construct('building-name')
        building = BuildingPrototype.create(person, name_forms=name)
        building.destroy()

        name_2 = Noun.fast_construct('building-name-2')
        building = BuildingPrototype.create(person, name_forms=name_2)

        self.assertNotEqual(old_version, buildings_storage.version)

        self.assertEqual(Building.objects.all().count(), 1)
        self.assertEqual(building.normalized_name, name_2)

    def test_amortize(self):
        building = BuildingPrototype.create(self.place_1.persons[0], name_forms=Noun.fast_construct('building-name'))

        old_integrity = building.integrity

        building.amortize(1000)

        self.assertTrue(old_integrity > building.integrity)

        building._model.integrity = 0

        building.amortize(1000)

        self.assertTrue(building.state._is_DESTROYED)


    def test_amortization_grows(self):
        building = BuildingPrototype.create(self.place_1.persons[0], name_forms=Noun.fast_construct('building-name'))

        old_integrity = building.integrity
        building.amortize(1000)
        amortization_delta = old_integrity - building.integrity

        building_2 = BuildingPrototype.create(self.place_1.persons[1], name_forms=Noun.fast_construct('building-name-2'))

        old_integrity_2 = building_2.integrity
        building_2.amortize(1000)
        amortization_delta_2 = old_integrity_2 - building_2.integrity

        self.assertTrue(amortization_delta < amortization_delta_2)

    def test_save__update_storage(self):
        building = BuildingPrototype.create(self.place_1.persons[0], name_forms=Noun.fast_construct('building-name'))

        old_version = buildings_storage.version
        building.save()
        self.assertNotEqual(old_version, buildings_storage.version)


    def test_destroy__update_storage(self):
        building = BuildingPrototype.create(self.place_1.persons[0], name_forms=Noun.fast_construct('building-name'))

        old_version = buildings_storage.version
        building.destroy()
        self.assertNotEqual(old_version, buildings_storage.version)
        self.assertFalse(building.id in buildings_storage)




class ResourceExchangeTests(testcase.TestCase):

    def setUp(self):
        super(ResourceExchangeTests, self).setUp()
        self.place_1, self.place_2, self.place_3 = create_test_map()

        self.resource_1 = random.choice(RESOURCE_EXCHANGE_TYPE._records)
        self.resource_2 = random.choice(RESOURCE_EXCHANGE_TYPE._records)

        self.exchange = ResourceExchangePrototype.create(place_1=self.place_1,
                                                         place_2=self.place_2,
                                                         resource_1=self.resource_1,
                                                         resource_2=self.resource_2,
                                                         bill=None)

    def test_create(self):
        self.assertEqual(self.exchange.place_1.id, self.place_1.id)
        self.assertEqual(self.exchange.place_2.id, self.place_2.id)
        self.assertEqual(self.exchange.resource_1, self.resource_1)
        self.assertEqual(self.exchange.resource_2, self.resource_2)
        self.assertEqual(self.exchange.bill_id, None)

    def test_get_resources_for_place__place_1(self):
        self.assertEqual(self.exchange.get_resources_for_place(self.place_1),
                         (self.resource_1, self.resource_2, self.place_2))

    def test_get_resources_for_place__place_2(self):
        self.assertEqual(self.exchange.get_resources_for_place(self.place_2),
                         (self.resource_2, self.resource_1, self.place_1))


    def test_get_resources_for_place__wrong_place(self):
        self.assertEqual(self.exchange.get_resources_for_place(self.place_3),
                         (RESOURCE_EXCHANGE_TYPE.NONE, RESOURCE_EXCHANGE_TYPE.NONE, None))
