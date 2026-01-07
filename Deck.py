import random
class Deck:
    """
    this class represents a deck of Black Jack cards.
    :parameter None
    :var deck: list of cards where each card is represented by a tuple of (int: suit, int rank)
    returns deck of black jack cards
    """
    def __init__(self):
        self.deck = [] # stores the 52 needed cards for the game
        for value in range(1, 14):
            for suit in range(0,4):
                self.deck.append((suit, value))


    def shuffle(self):
        """
            this function shuffles the deck
        """
        random.shuffle(self.deck)

    def deal(self):
        """"
        this function removes the top card from the deck and returns it
        """
        if len(self.deck) == 0:
            return None
        return self.deck.pop()

def get_card_value(card):
    """"
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


def decode_card(rank,suit):
    """
    Maps the suit integer to it's string representation, used to display the card for the client in a more informative way.
    """
    suit_map = {0: "Heart",1: "Diamond",2: "Clubs",3 : "Spades"}
    rank_map = {1: "Ace", 11: "Jack", 12: "Queen", 13: "King"}
    if rank < 2 or rank > 10:
        mapped_rank = rank_map[rank]
    else:
        mapped_rank = rank
    return suit_map[suit], mapped_rank
