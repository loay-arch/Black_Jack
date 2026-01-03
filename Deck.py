import random
class Deck:
    """
    docstring for Deck
    this class represents a deck of Black Jack cards.
    :parameter None
    :var deck: list of cards where each card is represented by a tuple of (str: suit, int rank)
    returns deck of black jack cards
    """
    def __init__(self):
        self.deck = [] # stores the 52 needed cards for the game
        suits = ['Clubs', 'Diamonds', 'Hearts', 'Spades']
        for suit in suits:
            for value in range(1, 14):
                self.deck.append((suit, value))


    def shuffle(self):
        """
        docstring for shuffle
        this function shuffles the deck
        """
        random.shuffle(self.deck)

    def deal(self):
        """"
        docstring for deal
        this function removes the top card from the deck and returns it
        """
        if len(self.deck) == 0:
            return None
        return self.deck.pop()

    def get_card_value(self, card):
        """"
        docstring for get_card_value
        this function returns the value of a card
        :parameter card: card that has a suit and a rank
        returns value of the card
        """
        if card[1] == 1:
            return 11
        elif card[1] > 10:
            return 10
        else:
            return card[1]

