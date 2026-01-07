import socket
from Deck import Deck, get_card_value, decode_card
from Protocol import pack_server_payload, unpack_client_payload, recv_exact


class ServerGameSession:
    """Manages the game logic for a single client's blackjack session."""

    def __init__(self, client_socket, rounds, client_name,server_name):
        self.client_socket = client_socket
        self.rounds = rounds
        self.client_name = client_name
        self.stats = {'wins': 0, 'losses': 0, 'ties': 0}
        self.rounds_played = 0
        self.server_name = server_name

    def play(self):
        """Run all rounds of blackjack."""
        print(f"\nStarting game with {self.client_name} for {self.rounds} rounds")
        for _ in range(self.rounds):
            try:
                self._play_round()
            except Exception as e:
                print(f'Continuing to send offers...')
                return
        self._display_final_stats()
        print(f'Continuing to send offers...')

    def _play_round(self):
        """Play a single round of blackjack."""
        deck = Deck()
        deck.shuffle()
        dealer_hand = []
        client_hand = []
        client_sum = 0
        dealer_sum = 0

        print(f"\n--- Round {self.rounds_played + 1} ---")

        # first give the client the first 2 cards
        for i in range(2):
            card = deck.deal()
            client_hand.append(card)
            client_sum += get_card_value(card)

            # i log the card being dealt
            card_str = self._format_card(card[1], card[0])
            print(f"{self.client_name} drew {card_str}")

            # rare but possible for the client to already busts ( if he receives 2 aces )
            result = 0x2 if (i == 1 and client_sum > 21) else 0x0
            # if busted send the client a message that he lost this round along side the last card which made him lose.
            self.client_socket.sendall(pack_server_payload(result, card[1], card[0]))

        # if busted end the round already
        if client_sum > 21:
            print(f"{self.client_name} busted with {client_sum}")
            self._display_hands(client_hand, dealer_hand)
            self._handle_round_end(2)  # Client loss
            return

        # deal initial dealer cards, but we only show the client the first one
        for i in range(2):
            card = deck.deal()
            dealer_hand.append(card)
            if i == 0:
                card_str = self._format_card(card[1], card[0])
                print(f"{self.server_name} drew {card_str}")
                self.client_socket.sendall(pack_server_payload(0x0, card[1], card[0]))
                # we did not add the hidden card value to the dealer sum because as long as its hidden we dont really care
                dealer_sum += get_card_value(card)
            else:
                card_str = self._format_card(card[1], card[0])
                print(f"{self.server_name} drew {card_str} (hidden)")


        self._display_hands(client_hand, dealer_hand, hide_dealer_second=True)


        while True:
            try:
                print(f'Waiting for {self.client_name} to decide his move')
                self.client_socket.settimeout(30)
                packet = recv_exact(self.client_socket, 10)
            except (socket.timeout, ConnectionError):
                print("Client timed out or disconnected during decision make")
                raise

            decision = unpack_client_payload(packet)
            print(f"{self.client_name} chose: {decision}")

            if decision == "Hit":
                card = deck.deal()
                client_hand.append(card)
                client_sum += get_card_value(card)

                card_str = self._format_card(card[1], card[0])
                print(f"{self.client_name} drew {card_str}")
                # client loses if its hand cards value is over 21
                result = 0x2 if client_sum > 21 else 0x0
                self.client_socket.sendall(pack_server_payload(result, card[1], card[0]))

                if result == 0x2:
                    print(f"{self.client_name} busted with {client_sum}")
                    self._display_hands(client_hand, dealer_hand)
                    self._handle_round_end(2)
                    break
                else:
                    self._display_hands(client_hand, dealer_hand, hide_dealer_second=True)

            elif decision == "Stand":
                print(f"{self.client_name} stands with {client_sum}")
                result = self._dealer_turn(dealer_hand, dealer_sum, client_sum, deck, client_hand)
                self._handle_round_end(result)
                break

    def _dealer_turn(self, dealer_hand, dealer_sum, client_sum, deck, client_hand):
        """Execute the dealer's turn."""
        print("\n--- Dealer's Turn ---")

        while True:
            # reveal current hidden card
            hidden = dealer_hand[-1]
            card_str = self._format_card(hidden[1], hidden[0])
            print(f"{self.server_name} drew {card_str}")

            # add its value to the dealer sum
            dealer_sum += get_card_value(hidden)

            # check if busted
            if dealer_sum > 21:
                result = 0x3  # Dealer busted, client wins
                print(f"{self.server_name} busted with {dealer_sum}")
            elif client_sum > dealer_sum:
                result = 0x3  # Client wins
            elif dealer_sum > client_sum:
                result = 0x2  # Dealer wins
            else:
                result = 0x1  # Tie

            if dealer_sum < 17:
                result = 0x0  # Keep playing

            # send the revealed card with correct result flag
            self.client_socket.sendall(pack_server_payload(result, hidden[1], hidden[0]))

            self._display_hands(client_hand, dealer_hand)

            # if round ended we stop
            if result != 0x0:
                if result == 0x1:
                    print(f"Tie! Both at {dealer_sum}")
                elif result == 0x2:
                    print(f"{self.server_name} wins! {self.server_name}: {dealer_sum}, {self.client_name}: {client_sum}")
                else:  # result == 0x3
                    print(f"{self.client_name} wins! {self.server_name}: {dealer_sum}, {self.client_name}: {client_sum}")
                return result

            # otherwise, draw next card but dont reveal it yet
            card = deck.deal()
            dealer_hand.append(card)

    def _format_card(self, rank, suit):
        """Convert rank and suit to readable card string."""
        card_suit, card_rank = decode_card(rank, suit)
        return f"{card_rank} of {card_suit}"

    def _display_hands(self, client_hand, dealer_hand, hide_dealer_second=False):
        """Display current hands."""
        client_hand_str = [self._format_card(card[1], card[0]) for card in client_hand]

        if hide_dealer_second and len(dealer_hand) > 1:
            dealer_hand_str = [self._format_card(dealer_hand[0][1], dealer_hand[0][0]), "[Hidden]"]
        else:
            dealer_hand_str = [self._format_card(card[1], card[0]) for card in dealer_hand]

        print(f"{self.client_name} hand: {client_hand_str}")
        print(f"{self.server_name} hand: {dealer_hand_str}\n")

    def _handle_round_end(self, result):
        """Handles end of round - update stats."""
        self.rounds_played += 1

        if result == 1:
            self.stats['ties'] += 1
            print(f"\nRound OVER: round ended in a tie.")
        elif result == 2:
            self.stats['losses'] += 1
            print(f"\nRound OVER: round ended in a loss (client lost).")
        else:  # result == 3
            self.stats['wins'] += 1
            print(f"\nRound OVER: round ended in a win (client won).")

    def _display_final_stats(self):
        """Display final game statistics."""
        print(f"\n{'=' * 50}")
        print(f"GAME OVER: STATISTICS FOR {self.client_name} AFTER {self.rounds} rounds")
        print(f"{self.client_name} wins: {self.stats['wins']} ({self.stats['wins'] / self.rounds * 100:.1f}%)")
        print(f"{self.client_name} losses: {self.stats['losses']} ({self.stats['losses'] / self.rounds * 100:.1f}%)")
        print(f"Ties: {self.stats['ties']} ({self.stats['ties'] / self.rounds * 100:.1f}%)")
        print(f"{'=' * 50}\n")