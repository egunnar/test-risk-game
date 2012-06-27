#!/usr/bin/python3.2
import unittest
import urllib.request 
import re
import json
import time
import sys

TEST_GAMES_DIR = 'test'
GAME_URL = r'http://localhost:8888/server_game'
LOG_URL = r'http://localhost:8888/log'
LOW_DICE = 500
TID2NAME = {
    "alaska":0,
    "greenland":1,
    "northwest_territory":2,
    "alberta":3,
    "ontario":4,
    "quebec":5,
    "western_us":6,
    "eastern_us":7,
    "central_america":8,
    "venezuela":9,
    "peru":10,
    "brazil":11,
    "argentina":12,
    "north_africa":13,
    "egypt":14,
    "east_africa":15,
    "congo":16,
    "south_africa":17,
    "madagascar":18,
    "scandinavia":19,
    "western_europe":20,
    "great_britain":21,
    "southern_europe":22,
    "northern_europe":23,
    "ukraine":24,
    "iceland":25,
    "ural":26,
    "siberia":27,
    "afghanistan":28,
    "middle_east":29,
    "irkutsk":30,
    "kamchatka":31,
    "yakutsk":32,
    "japan":33,
    "siam":34,
    "mongolia":35,
    "china":36,
    "india":37,
    "indonesia":38,
    "new_guinea":39,
    "western_australia":40,
    "eastern_australia":41
}

class MyTest(unittest.TestCase):

    def setUp(self):
        reset_to_standard_1000_dice()

    def tearDown(self):
        pass

    def testBasicLoadGameAndAttack(self):
        '''Test 1) loading a basic game 2)pushing on dice 3)attacking a
        territory 4) after winning that territory moving in troops'''

        # I'm player 2 (green). going to attack from northern europe (5 armies)
        # to ukraine which is blue and has 1 armies
        self.load_game('testBasicLoadGameAndAttack.json')

        
        # attack the territory (the attacker will win)
        response = call_game_server('frisk.api_attack(23, 24, 4)');

        # api_post_attack_move(from_tid, to_tid, armies, all_armies){
        response = call_game_server('frisk.api_post_attack_move(23, 24, 4)');

        response = call_game_server('frisk.api_get_territories()');
        territories = json.loads(response['body'])
        self.confirmTerritories((
            { 'tid':23, 'owning_player':2, 'exception_message': 'orig territory still mine'},
            { 'tid':24, 'owning_player':2, 'exception_message': 'attack territory mine'},
            { 'tid':23, 'current_armies':1, 'exception_message': 'orig territory armies correct'},
            { 'tid':24, 'current_armies':4, 'exception_message': 'attack territory armies correct'},

        ))

    def testMediumPath(self):
        ''' Test that can knock off player with all the action happening in 
        2 islands. the human player has all of australia, north america, and
        africa (save south_africa). the AI has everything else. it has 200 
        armies on kamchatka (should be used to wipe out one island) and 20 
        armies on siam.'''
        self.load_game('testMediumPath.json');

        call_game_server('frisk.api_set_next_turn()')

        self.waitForHumanTurn()
        self.confirm_player_won(0)

    def confirm_player_won(self, pid):
        ''' confirm that pid own the game '''
        confirm_data = [];
        for tid in range(0, 42):
            confirm_data.append(
                { 'tid':tid, 'owning_player':pid, 'current_armies':'+1'})
        self.confirmTerritories(confirm_data)


    def testAfricaPath(self):
        ''' Test that can knock off player with all the action happening in 
        one continent (africa). the AI has the entire world and north africa
        with alot of armies in north africa. the other player has 1 army in
        every other square'''
        self.load_game('testAfricaPath.json');

        call_game_server('frisk.api_set_next_turn()')

        self.waitForHumanTurn()

        self.confirmTerritories((
            { 'tid_name':'north_africa', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'egypt', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'east_africa', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'congo', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'south_africa', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'madagascar', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'middle_east', 'owning_player':0, 'current_armies':'+1'},
        ))

    def testEastFakeContinentPath(self):
        ''' Test that can knock off player. The only correct path is so I 
        have to go through the fake continent extra_cont_east.  
        '''

        self.load_game('testEastFakeContinentPath.json');

        call_game_server('frisk.api_set_next_turn()')

        self.waitForHumanTurn()
        self.confirm_player_won(0)

    def testAPIErrorHandling(self):
        ''' Basic test that this script fails if a application error is returned
        from api.js'''

        re_obj = re.compile(r'frisk.api_attack.*? in api.js raised error 2')
        with self.assertRaisesRegex(Exception, re_obj):
            call_game_server('frisk.api_attack()')

    # AI tests below
    ################################
    def testAIMostBasicWin(self):
        ''' Only 2 players (player 0 computer/ player 1 human) and it's human
        reinforce turn. AI owns everything but south america. Confirm AI put
        all armies on central america and attack all square of the other 
        player for win. I say central america and not north africa because 
        central america already has 3 armies to leverage, north africa has 1. 
        '''

        self.load_game('testAIMostBasicWin.json');

        call_game_server('frisk.api_set_next_turn()')

        self.waitForHumanTurn()

        self.confirmTerritories((
            { 'tid_name':'central_america', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'venezuela', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'peru', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'brazil', 'owning_player':0, 'current_armies':'+1'},
        ))

    def testAI2IslandWin(self):
        ''' Only 2 players (player 0 computer/ player 1 human) and it's human
        reinforce turn. AI owns everything but south america and australia. 
        like testAIMostBasicWin but 2 islands to conquered. i have the
        territories so austrilia and south america would require about the same
        amount of armies to conquer. confirm AI amount armies for on 
        siam and on central america (considering armies already there)'''

        self.load_game('testAI2IslandWin.json');
        call_game_server('frisk.api_set_next_turn()')
        self.waitForHumanTurn()

        response = call_game_server('frisk.api_get_number_of_alive_players()')
        alive_players = json.loads(response['body'])
        debug('alive_players:{}'.format(alive_players))
        self.assertEqual(alive_players, 1, 'conquered the two islands')
        self.confirmTerritories((
            { 'tid_name':'central_america', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'venezuela', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'peru', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'brazil', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'indonesia', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'new_guinea', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'western_australia', 'owning_player':0, 'current_armies':'+1'},
            { 'tid_name':'eastern_australia', 'owning_player':0, 'current_armies':'+1'}
        ))

        # confirm that central america was reinforced with 17 units and siam 
        # with 14
        all_moves = json.loads(call_game_server('frisk.get_log_api_calls()')['body'])
        hit_siam_14 = False
        hit_central_america_17 = False
        for api_move in (all_moves):
            debug(api_move)
            if re.search(r'api_reinforce\({0},14\)'.format(TID2NAME['siam']), api_move):
                hit_siam_14 = True
            if re.search(r'api_reinforce\({0},17\)'.format(TID2NAME['central_america']), api_move):
                hit_central_america_17 = True
        self.assertTrue(hit_siam_14, 'reinforced siam with 14 units')
        self.assertTrue(hit_central_america_17, 'reinforced central america  with 17 units')

    def testStressPath(self):
        ''' Only 2 players (player 0 computer/ player 1 human) and it's human
        reinforce turn. AI ownes only western australia with 500 armies. Every
        other square has 1 army on it. The AI should win the win. This test is
        generally test the performance of my path finding'''

        self.load_game('testStressPath.json');
        call_game_server('frisk.api_set_next_turn()')
        self.waitForHumanTurn()
        self.confirm_player_won(0)

    def testAddExtraPath(self):
        ''' 3 players. red (player 0) is human and owns all of europe, africa,
        australia, asia, and territory of central america. blue (player 1)
        owns only alaska with 50 armies. green owns everything else. the 
        essense of the test is that AI is smart enough to go through the
        central america to wipe out green'''

        self.load_game('testAddExtraPath.json');
        call_game_server('frisk.api_set_next_turn()')
        self.waitForHumanTurn()

        # confirm green is destory
        response = call_game_server('frisk.api_get_number_of_alive_players()')
        alive_players = json.loads(response['body'])
        debug('alive_players:{}'.format(alive_players))
        self.assertEqual(alive_players, 2, 'knocked off green player')

    def testPickWipeOutPlayer(self):
        ''' 3 players. red (player 0) is human and owns all of europe, africa,
        australia, asia. blue (player 1) owns only alaska with 50 armies. 
        green owns everything else. red has over 300 armies on the board. 
        essense of the test is that AI is smart enough knock off green.'''

        self.load_game('testPickWipeOutPlayer.json');
        call_game_server('frisk.api_set_next_turn()')
        self.waitForHumanTurn()

        # confirm green is destory
        response = call_game_server('frisk.api_get_number_of_alive_players()')
        alive_players = json.loads(response['body'])
        debug('alive_players:{}'.format(alive_players))
        self.assertEqual(alive_players, 2, 'knocked off green player')


    def testEasyStressPath(self):
        ''' Having issues with testStressPath so trying something easier first.
        Just conquering africe from Western Europe'''

        self.load_game('testEasyStressPath.json');
        call_game_server('frisk.api_set_next_turn()')
        self.waitForHumanTurn()

        response = call_game_server('frisk.api_get_number_of_alive_players()')
        alive_players = json.loads(response['body'])
        debug('alive_players:{}'.format(alive_players))
        self.assertEqual(alive_players, 1, 'conquered the two islands')


    def load_game(self, game_file):
        ''' '''
        full_game_file = '{0}/{1}'.format(TEST_GAMES_DIR, game_file)
        debug('full_game_file is:' + full_game_file);
        fh = open(full_game_file, 'r');
        game_data = fh.readline()
        fh.close()
        call_game_server('frisk.api_load_game(' + game_data + ')');
        call_game_server('frisk.turn_on_log_api_calls()');
        call_game_server('frisk.reset_log_api_calls()');
    
    # FIXME 100% confident this really works
    def waitForHumanTurn(self):
        ''' return after the AI is done. keep polling it's a human turn'''

        MAX_SLEEP_TIME_FOR_AI_MOVE = 3
        start_time = time.time()
        while (time.time() - start_time) < MAX_SLEEP_TIME_FOR_AI_MOVE:
            time.sleep(.1)
 
            # get the alive human players and if none just return
            body = call_game_server('frisk.api_get_players()')['body']
            players_array = json.loads(body)
            alive_players_set = {i for i in players_array if i['is_human'] and
                    i['is_alive']}
            if (len(alive_players_set) == 0):
                return

            # am in on any of the human player turns
            body = call_game_server('frisk.api_get_turn_info()')['body']
            player_index = json.loads(response['body'])['player_index']
            if players_array[player_index].is_human:
                return
        return

    def confirmTerritories(self, expected_territories):
        ''' check the state of the territories against expected_territories
        argument. expected_territories is list with hash elements. each element
        can has the following:
            tid_name or tid
            owning_player -> optional  
            current_armies -> optional. can be a number or string with a + or -
                in front. '+5' means atleast 5 armies
        '''
        debug('expected_territories:' + str(expected_territories))
        response = call_game_server('frisk.api_get_territories()');
        territories = json.loads(response['body'])
        for check in (expected_territories):
            self.checkATerritory(check, territories)

    def checkATerritory(self, check, territories):
        tid = None
        debug('check:' + str(check))
        if 'tid_name' in check:
            tid = TID2NAME[check['tid_name']]
        elif 'tid' in check:
            tid = check['tid'] 
        else:
            raise Exception('invalid call to confirmTerritories')
        debug('using tid:' + str(tid))
        debug('checking territory:' + get_tid_name(tid))

        if 'owning_player' in check:
            self.checkATerritoryAttribute(check, 'owning_player', tid, territories)
        if 'current_armies' in check:
            self.checkATerritoryAttribute(check, 'current_armies', tid, territories)


    def checkATerritoryAttribute(self, check, attribute, tid, territories):
        territory = territories[tid]
        debug('territory is:' + str(territory))
        exception_message = 'territory {0} attribute {1} expected {2} and got {3}'.format(get_tid_name(tid), attribute, check[attribute],
            territory[attribute])
        if ('exception_message' in check):
            exception_message = check['exception_message']
        debug('my exception_message:' + str(exception_message))
        if attribute == 'owning_player': 
            self.assertEqual(check['owning_player'], territory['owning_player'], exception_message)
        elif attribute == 'current_armies' and (type(check[attribute]) == str): 
            match_obj = re.match(r'^\+(\d+)$', check[attribute]) 
            if match_obj:
                self.assertLessEqual(float(match_obj.group(1)), territory[attribute], exception_message)
                return
            match_obj = re.match(r'^-(\d+)$', check[attribute]) 
            if match_obj:
                self.assertGreaterEqual(float(match_obj.group(1)), territory[attribute], exception_message)
                return

            self.fail('current_armies check is {0} and is not valid'.format(check[attribute]))
        elif attribute == 'current_armies' and (type(check[attribute]) == int): 
            self.assertEqual(check['current_armies'], territory[attribute], exception_message)

def get_tid_name(tid):
    for (k, v) in TID2NAME.items():
        if (v == tid):
            debug("returning:" + k)
            return k;

def reset_to_standard_1000_dice():
        call_game_server('frisk.api_reset_dice_roll_array()')

        fh = open(TEST_GAMES_DIR + '/1000_dice.txt', 'r')
        dice = fh.read()
        fh.close()
        response = call_game_server('frisk.api_push_dice_rolls(' + dice + ')');

       
def push_dice_if_need():
        response = call_game_server('frisk.api_get_dice_left()')
        dice_left = response['body'].strip()
        if (not re.match('\d+$', dice_left)):
            raise Exception('frisk.api_get_dice_left() invalid response was ' +
                response['body'].strip())
        
        if (int(dice_left) < LOW_DICE):
            fh = open(TEST_GAMES_DIR + '/1000_dice.txt', 'r')
            dice = fh.read()
            fh.close()
            response = call_game_server('frisk.api_push_dice_rolls(' + dice + ')');


def call_game_server(data):
    # see http://docs.python.org/py3k/library/urllib.request.html#examples
    req = urllib.request.urlopen(GAME_URL, data.encode('utf-8'))
    body = req.read().decode('utf-8')
    if req.getcode() != 200:
        debug('non 200 status returned')
        raise Exception('non 200 status returned from:' + data)
    if len(body) > 0:
        eval_body = json.loads(body)
        if type(eval_body) == dict:
            if 'error' in eval_body:
                err_message = '{} in api.js raised error {}'.format(data, eval_body['error'])
                debug('api exception:' + err_message)
                raise Exception(err_message)
    return {'body':body, 'code':req.getcode()}

def debug(message):
    if type(message) != str:
        message = str(message)
    sys.stderr.write(message + "\n")

if __name__ == '__main__':

    unittest.main()
    '''
    suiteFew = unittest.TestSuite()
    suiteFew.addTest(MyTest("testBasicLoadGameAndAttack"))
    suiteFew.addTest(MyTest("testAIMostBasicWin"))
    suiteFew.addTest(MyTest("testAfricaPath"))

    suiteFew.addTest(MyTest("testAPIErrorHandling"))
    suiteFew.addTest(MyTest("testAI2IslandWin"))
    suiteFew.addTest(MyTest("testMediumPath"))
    
    suiteFew.addTest(MyTest("testEasyStressPath"))
    suiteFew.addTest(MyTest("testEastFakeContinentPath"))
    suiteFew.addTest(MyTest("testStressPath"))
    #suiteFew.addTest(MyTest("testAddExtraPath"))

    # testStressPath
    unittest.TextTestRunner(verbosity=2).run(suiteFew)
    '''
