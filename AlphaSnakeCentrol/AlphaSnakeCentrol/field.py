import numpy as np
import copy
'''
    This part controls the update of the field. Defining field matrix as follows:
        x means the row index, y means the column index
            +------------------------------------------->(y)
            |
            |
            |
            |                   0
            |                   |
            |              3 ---*--- 1
            |                   |
            |                   2
            |
            |
            |
            |
            V(x)
'''
GoUndefined = -1    # only for player died
GoUp = 0
GoRight = 1
GoDown = 2
GoLeft = 3

class Snake():
    '''
        Use to record user state, not for external use
    '''
    def __init__(self, head=None):
        self.state = 1
        if head == None:
            self.body = []
        else:
            self.body = [head]

    def head(self):
        return self.body[0]

    def tail(self):
        return self.body[-1]

    def die(self):
        self.state = 0

class Field():
    '''
        The object Field update it state by calling 'go' method, which takes in the movement of each participant
    and return the whole map and the users' state after this iteration.
        User ID start at 1
        User state: 0: dead, 1: alive
        Food: -1 on the map
    '''
    def __init__(self, num_users, num_foods= 2, map_size=(100, 100), dead2food= False):
        '''
            Given information to setup the field to start the game.
            Set the number un-eaten food in num_foods argument
        '''
        # The map contains 100*100 bytes which represents the state of the pixel (occupied by user or food or
        # unoccupied)
        self.map = np.zeros(map_size, dtype=np.int8)

        # A list using user ID (a positive number) as index, a tuple as value which contains the state of the
        # user and the body (a list of coordinates) of the snake. index 0 gets the head coordinate.
        self.users = [Snake()]

        # setup whether needed to change dead body to food
        self.dead2food = dead2food

        # initializing map and user state
        for i in range(1, num_users+1):
            # generate coordinates without conflict with the initial map
            x = np.random.randint(0, map_size[0])
            y = np.random.randint(0, map_size[1])
            while self.map[x, y] != 0:
                x = np.random.randint(0, map_size[0])
                y = np.random.randint(0, map_size[1])

            # set map and user info
            self.map[x, y] = 2 * i;
            self.users.append(Snake(head= (x, y)))

        # set food on the map
        for i in range(num_foods):
            x = np.random.randint(0, map_size[0])
            y = np.random.randint(0, map_size[1])
            while self.map[x, y] != 0:
                x = np.random.randint(0, map_size[0])
                y = np.random.randint(0, map_size[1])
            self.map[x, y] = -1

    def eat_food(self, uid, move)->bool:
        '''
            DO NOT call this function externally.
            It checks whether this movement will make this user eat a food.
        '''
        coord = self.users[uid].body[0]
        if move == GoUp:
            return self.map[coord[0] - 1, coord[1]] == -1
        elif move == GoRight:
            return self.map[coord[0], coord[1] + 1] == -1
        elif move == GoDown:
            return self.map[coord[0] + 1, coord[1]] == -1
        elif move == GoLeft:
            return self.map[coord[0], coord[1] - 1] == -1
        else:
            return False

    def hit_body(self, uid, move)->bool:
        '''
            DO NOT call this externally.
            To check if the user hit a body of on the map, not only check the pixel to go whether is a body (odd
        value), but also check if is a head whose user_id smaller than this in terms of the body state updating
        sequence.
            Because when head crush together, it should be two user die.
        '''
        user_coordinate = self.users[uid].head()
        target = copy(user_coordinate)
        if move == GoUp:
            target[0] -= 1
        elif move == GoRight:
            target[1] += 1
        elif move == GoDown:
            target[0] += 1
        elif move == GoLeft:
            target[1] -= 1
        else:
            return False

        # check if the request is out side of the map
        if target[0] < 0 or target[0] >= self.map.shape()[0] or target[1] < 0 or target[1] >= self.map.shape()[1]:
            self.users[uid].die()
            return True

        if self.map[target] <= 0:
            return False

        # Could crush into other user
        crush_uid = (self.map[target] + 1) // 2
        if self.map[target] % 2 != 0:
            # This is not a head, but could be a tail
            if crush_uid < uid:
                self.users[uid].die()
                return True
            elif target != self.users[crush_uid].tail():
                self.users[uid].die()
                return True
            else:
                return False

        if crush_uid < uid:
            # two head crush together occasion
            self.users[crush_uid].die()
            self.users[uid].die()
            return True
        elif len(self.users[crush_uid].body) > 1:
            # hit the neck of other users 23333
            self.users[uid].die()
            return True
        else:
            # just pass the user with length 1, so close
            return False
        
    def move_body(self, uid, move, ate):
        '''
            DO NOT call this function externally
            move the body of given user
        '''        
        user_coordinate = self.users[uid].head()
        target = copy(user_coordinate)
        if move == GoUp:
            target[0] -= 1
        elif move == GoRight:
            target[1] += 1
        elif move == GoDown:
            target[0] += 1
        elif move == GoLeft:
            target[1] -= 1
        else:
            return

        if not ate:
            self.map[self.users[uid].tail()] == 0
            self.users[uid].body.pop()
        if len(self.users[uid].body) > 0:
            self.map[self.users[uid].head()] -= 1

        self.users[uid].body.insert(0, target)
        self.map[self.users[uid].head()] = 2 * uid


    def go(self, moves=None):
        '''
            Given the movement of each participant, return the whole map and a dictionary of participants' states.
            moves: a list with participants' ID as index (start from 1) and a number (0,1,2,3) as value indicates
        the moving direction.
            return: a matrix represented in a 2D array
                and a list with participants' ID (a positive number) as index and a number representing state
        ''' 
        # make sure the lengh of the list is the number of users
        assert len(moves) == len(self.users), "Diffreent input length as declared number of users"

        food_eaten = 0
        # iterate each users to move the snake
        for i in range(1, len(self.users)):
            if not self.users[i].state:
                continue # if user is dead
            will_eat = self.eat_food(i, moves[i])
            died = self.hit_body(i, moves[i])
            if not died:
                if will_eat:
                    food_eaten += 1
                self.move_body(i, moves[i], will_eat)
            else:
                # prevent the death distrubing the judgement
                self.map[self.users[i].head()] = 2 * i - 1

        if self.dead2food:
            # change all the dead body to food and remove the user info (length to 0)
            pass

        # check if food is less
        for i in range(food_eaten):
            # generate food at random location
            x = np.random.randint(0, map_size[0])
            y = np.random.randint(0, map_size[1])
            while self.map[x, y] != 0:
                x = np.random.randint(0, map_size[0])
                y = np.random.randint(0, map_size[1])
            self.map[(x, y)] = -1
            
        # return the state of the field and the users states
        states = [user.state for user in self.users]
        return (self.map, states)