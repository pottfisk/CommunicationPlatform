# Communication Platform - Server
from flask import Flask
import socketio
import time

# Object Created by developers to start a server that listen for clients to connect
class CommunicationServer():  # External
  def __init__(self, maxConcurr=8):
    self.MaxConcurrentClients = maxConcurr
    self.Clients = []
    self.sio = socketio.Server()
    self.app = None
    self.Games = []

  def __removeClientById(self, sid):
    for client in self.Clients:
      if client.compare(sid):
        self.Clients.remove(client)

  #All socketIO callbacks
  def __callbacks(self):

    @self.sio.event
    def connect(sid, environ, auth):
      if len(self.Clients) >= self.MaxConcurrentClients:
        self.sio.emit('server_full', to=sid)
        self.sio.disconnect(sid)
      else:
        new_client = Client(sid)
        self.Clients.append(new_client)
        print('Clients connected: ' + str(len(self.Clients))) # Ugly print

    @self.sio.event
    def disconnect(sid):
      self.__removeClientById(sid)
      print('Clients connected: ' + str(len(self.Clients)))

    @self.sio.event
    def message(sid, data):
      print('received message: ' + data + ' from ' + sid)

    @self.sio.event
    def msg_to_opponent(sid, data):
      print('msg_to_opponent: ' + data + ' from ' + sid)
      #print('Clients: ' + str(len(self.Clients)))
      #print(self.Clients[0].get_id())

      player_in_game = False
      opponent = None
      for game in self.Games:
        if (sid == game.PlayerA.get_id() or sid == game.PlayerB.get_id()) and game.Active: # the player 'sid' is playing in the game and the game is still going on
          player_in_game = True
          if sid == game.PlayerA.get_id():
            opponent = game.PlayerB.get_id()
          else:
            opponent = game.PlayerA.get_id()
          break

      print('player_in_game: ' + str(player_in_game) + ' opponent: ' + str(opponent))
      if player_in_game:
        #self.sio.emit('msg_to_opponent', 'Your message got sent to opponent ' + opponent + '.', to=sid) # response to the one calling
        self.sio.emit('msg_to_opponent', '0', to=sid) # response to the one calling
        self.sio.emit('msg_from_opponent', 'Opponent ' + sid + ' sent "' + data + '".', to=opponent)
        print('message sent to from ' + sid + ' to opponent ' + opponent)
      else:
        #self.sio.emit('msg_to_opponent', 'You are not in a game, no opponent exists.', to=sid)
        self.sio.emit('msg_to_opponent', '-1', to=sid)
        print('Player: ' + sid + ' is not in game, msg_to_opponent.')

    @self.sio.event
    def start_game_request(sid):
      print('start_game_request: from ' + sid)
      code = self.StartGame()
      self.sio.emit('start_game_request', str(code), to=sid)

    @self.sio.event
    def ready(sid):
      print('ready: from ' + sid)

      # Sets client.Ready to true
      for client in self.Clients:
        if client.compare(sid):
          client.Ready = True
          self.sio.emit('ready', str(0), to=sid)
          break
      # NOTE: Currently does not have the case if sending -1 (fail) for a ready() call


      # Check if all players are ready, if they are we start a game!
      ready_counter = 0
      for client in self.Clients:
        if client.Ready:
          ready_counter += 1

      if ready_counter == len(self.Clients): # everyone is ready
        code = self.StartGame()
      else:
        print('Players Ready: ' + str(ready_counter) + '/' + str(len(self.Clients)) + ', waiting for all.')


  def CreateServer(self, ip, port):
    self.app = Flask(__name__)
    self.app.wsgi_app = socketio.WSGIApp(self.sio, self.app.wsgi_app)
    self.__callbacks()
    self.app.run(ip, port)

  def StartGame(self):
    if len(self.Games) != 0:
      print("Cannot start a new game, a game is already going on.")
      return -1

    print("------STARTING A GAME------")
    # Starts a game, different cases based on number of players
    if len(self.Clients) == 1:
      # only 1 player, start AI match
      print("Starting AI Game (not implemented)")
      return -1
    if len(self.Clients) == 2:
      # 2 players, match them up for a game
      game = Game(self.Clients[0], self.Clients[1], True)
      print(game)
      print('Started Game: ' + str(game.PlayerA) + ' vs ' + str(game.PlayerB) + '.')
      self.sio.emit('game_info', 'you are now in a game vs ' + game.PlayerB.get_id(), to=game.PlayerA.get_id()) # msg PlayerA that they are playing vs PlayerB
      self.sio.emit('game_info', 'you are now in a game vs ' + game.PlayerA.get_id(), to=game.PlayerB.get_id()) # vice-versa

    if len(self.Clients) > 2:
      # more than 2 players, match 2 up and put the rest in a queue
      print("Starting a game and putting players in a queue (not implemented)")
      return -1

    self.Games.append(game)
    return 0


class Client:
  def __init__(self, ID):
    self.ID = ID
    self.Ready = False
    self.PlayerInfo = PlayerInfo()

  def __str__(self):
    return '[SID: ' + self.ID + ']' # might want to add playerinfo here later on

  def compare(self, sid):
    return sid == self.ID

  def get_id(self):
    return self.ID


class PlayerInfo:
  def __init__(self):
    GamesPlayed = 0
    GamesLeft = 0
    NumberOfWins = 0

  # Send the PlayerInfo to the player via the Socket
  def SendStatistics():
    pass

class Game:
  def __init__(self, PlayerA=None, PlayerB=None, Active=False, Winner=None):
    self.PlayerA = PlayerA
    self.PlayerB = PlayerB
    self.Active = Active
    self.Winner = Winner

  def __str__(self):
    return 'PlayerA: ' + str(self.PlayerA) + '\n' \
    + 'PlayerB: ' + str(self.PlayerB) + '\n' \
    + 'Active: ' + str(self.Active) + '\n' \
    + 'Winner: ' + str(self.Winner) + '\n' \
    + '----------------------------'

if __name__ == "__main__":
  cs = CommunicationServer(8)
  cs.CreateServer('127.0.0.1', 5000)