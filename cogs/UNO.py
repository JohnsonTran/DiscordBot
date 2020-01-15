import discord
import asyncio
from discord.ext import commands
from random import shuffle


# deals players 7 cards to setup the game
def start_game(deck, player_list):
    deck.shuffle()
    for num in range(7):
        for player in player_list:
            deck.deal(player)


# TODO: DM the player for input and use reactions for the cards. 1-10 and A-I for the cards (19 cards) and right arrow for draw
# TODO: When the player has 19 cards, their turn is skipped unless they can play a card
# asks the player what they want to do for their turn
def get_player_action(curr_player, card_in_play, curr_color):
    valid = False
    # keeps asking the player for input until they give a valid input: "DRAW" or an index of a card in their hand
    while not valid:
        try:
            action = input("What card do you want to play? 0-" + str(len(curr_player.hand) - 1) +
                           "\nor type 'DRAW' to draw a card\n")
            valid = action.upper() == "DRAW" or 0 <= int(action) < len(curr_player.hand)
        except ValueError:  # when the player inputs anything that is not "DRAW" or a number
            print("Not a valid input")
            print("The current card is {} and the current color is {}".format(card_in_play, curr_color))
            curr_player.print_hand()
    return action


# gets the index of next player based on the current index and if a reverse has been played
def get_next_player(player_list, index, reverse):
    return (index - 1) % len(player_list) if reverse else (index + 1) % len(player_list)


# changes the color based on the player's choice (used for WILD card)
def color_change(curr_color, index):
    while True:
        curr_color = input("What color do you want to change it to?: RED, YELLOW, GREEN, or BLUE\n").upper()
        if curr_color == "RED" or curr_color == "YELLOW" or curr_color == "GREEN" or curr_color == "BLUE":
            break
    print("Player {} changed the color to {}".format(index + 1, curr_color))


# deals with action cards
def handle_action_card(card, deck, p_list, reverse, index, next_player_index, curr_color):
    if card.value == "REVERSE":
        # reverse the cycle
        reverse = not reverse
        next_player_index = get_next_player(p_list, index, reverse)
    elif card.value == "+2":
        for i in range(2):
            deck.deal(p_list[next_player_index])
        # skips the next player
        next_player_index = get_next_player(p_list, next_player_index, reverse)
    elif card.value == "+4":
        for i in range(4):
            deck.deal(p_list[next_player_index])
        # skips the next player
        next_player_index = get_next_player(p_list, next_player_index, reverse)
        color_change(curr_color, index)
    elif card.value == "SKIP":
        # skips the next player
        next_player_index = get_next_player(p_list, next_player_index, reverse)
    elif card.value == "WILD":
        color_change(curr_color, index)


# determines if there is a winner
def winner(player_list):
    for player in player_list:
        if len(player.hand) == 0:
            return True
    return False


class UNO(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("UNO is ready to go")

    # command to play UNO
    @commands.command()
    async def play(self, ctx):
        msg = await ctx.send("Want to play UNO? React to the message to queue up!")
        await msg.add_reaction("\U0001F44D")
        await asyncio.sleep(5)
        cache_msg = await ctx.channel.fetch_message(msg.id)
        reaction = cache_msg.reactions[0]
        users = await reaction.users().flatten()
        users.pop(0)  # gets rid of the bot that reacted to the message
        await ctx.send("The players of this game are:")
        for user in users:
            await ctx.send(user.mention)

        # ***uncomment if considering other reactions***
        # players = []
        # for reaction in cache_msg.reactions:
        #     async for user in reaction.users():
        #         players.append(user)
        # print(players)

        # game setup
        deck = Deck()
        player_list = []
        for user in users:
            player_list.append(Player(user))
        start_game(deck, player_list)
        index = 0
        deck.setup()
        curr_color = deck.discard[0].color
        reverse = False
        curr_player = player_list[index]
        # plays the game
        while not winner(player_list):
            card_in_play = deck.discard[len(deck.discard) - 1]
            print("It is Player " + str(index + 1) + "'s turn")
            print("The current card is:", card_in_play)
            curr_player.print_hand()
            # get input from the player
            while True:
                next_player_index = get_next_player(player_list, index, reverse)
                action = get_player_action(curr_player, card_in_play, curr_color)
                if action.upper() == "DRAW":
                    deck.deal(curr_player)
                    card = card_in_play  # used to fix bug for drawing on the first turn
                    break
                elif 0 <= int(action) < len(curr_player.hand):
                    card = curr_player.hand[int(action)]
                    # check if the card is playable
                    if card.can_play(card_in_play) or card.can_play_color(curr_color):
                        # plays the card
                        curr_player.hand.remove(card)
                        deck.discard.append(card)
                        # do special card actions
                        handle_action_card(card, deck, player_list, reverse, index, next_player_index, curr_color)
                        break  # end of player's turn, got a valid move
                    else:  # the player chose a card that is not playable based on the current card
                        print("This is not a valid card")
                        print("The current card is {} and the current color is {}".format(card_in_play, curr_color))
                        curr_player.print_hand()
            index = next_player_index
            curr_player = player_list[next_player_index]
            # used to change the color when a WILD card is played
            curr_color = card.color if card.color != "BLACK" else curr_color
        # displays the winner
        winner_index = 0
        while len(player_list[winner_index].hand) != 0 and winner_index < len(player_list):
            winner_index += 1
        print("The winner is Player", winner_index + 1)



def setup(client):
    client.add_cog(UNO(client))


# UNO game classes
# Card class to represent the cards for the game
# TODO: represent the cards as emojis 
class Card:

    # initializer that creates card with value, color, and special ability
    def __init__ (self, value, color, special):
        self.value = value  # should be a string
        self.color = color
        self.special = special

    # getter methods
    def get_value(self):
        return self.value

    def get_color(self):
        return self.color

    def get_special(self):
        return self.special

    # determines if this card can be played based on another card (should be card in play)
    def can_play(self, card):
        # a card can get played if it shares the same value or color as the current card in play
        # a black card (WILD) can be played at all times
        return self.value == card.value or self.color == card.color or self.color == "BLACK"

    # determines if this card can be played based on a color (this is for WILD cards)
    def can_play_color(self, color):
        return self.color == color

    # representation of the card
    def __repr__(self):
        return self.color + " " + self.value


# Deck class that represents the deck and all the cards for the game
class Deck:

    def __init__(self):
        self.deck = []
        self.discard = []
        # makes the deck of cards
        color = ["RED", "YELLOW", "GREEN", "BLUE"]
        for i in range(4):
            # 1 0 for every color
            self.deck.append(Card("0", color[i], ""))
            for j in range(1, 10):
                # 2 1-9 for every color
                self.deck.append(Card(str(j), color[i], ""))
                self.deck.append(Card(str(j), color[i], ""))
            # 2 draw 2, skip, and reverses for every color
            for j in range(2):
                self.deck.append(Card("+2", color[i], "Draw 2 cards"))
                self.deck.append(Card("SKIP", color[i], "Skip next player's turn"))
                self.deck.append(Card("REVERSE", color[i], "Reverse the player order"))
        # 4 wild and draw 4 for the deck
        for i in range(4):
            self.deck.append(Card("WILD", "BLACK", "Choose any color"))
            self.deck.append(Card("+4", "BLACK", "Draw 4 cards and choose any color"))

    # shuffles the deck
    def shuffle(self):
        shuffle(self.deck)

    # gives a specified player a card
    def deal(self, player):
        player.hand.append(self.deck.pop())

    # sets up the first card of the game, changes the card if the first card is WILD
    def setup(self):
        first_card = self.deck.pop()
        while first_card.color == "BLACK":
            self.deck.append(first_card)
            shuffle()
        self.discard.append(first_card)


# Player class to represent data for the player
class Player:

    def __init__(self, member):
        self.hand = []
        self.discord_member = member

    # gets a card from the deck
    def draw(self):
        Deck.deal(self)

    # plays the specified card
    def play(self, index):
        if self.hand[index].can_play(Deck.deck[len(Deck.deck)]):
            return self.hand[index]
        else:
            return None

    # prints the cards in the player's hand
    def print_hand(self):
        print("Your hand:", self.hand)