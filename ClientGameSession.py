import socket
from Protocol import request_Message, unpack_server_payload, pack_Client_Payload, recv_exact
from Deck import decode_card
from enum import Enum


class Phase(Enum):
    P_INIT = "P_INIT"  # represents the phase in the game where its the client turn to receive 2 cards in a row ( game just started )
    D_UP = "D_UP"  # represents the phase in the game where its the dealer turn to receive 2 cards in a row ( we show only first one )
    P_TURN = "P_TURN"  # represents the phase in the game where its the client turn mid game ( client chooses hit or stand )
    D_TURN = "D_TURN"  # represents the phase in the game where the client chose stand and its dealer turn to receive cards


class ClientGameSession:
    """Manages the gameplay logic for the client side."""

    def __init__(self, tcp_socket, server_name):
        self.tcp_socket = tcp_socket
        self.client_name = "Just_One_More_Hit"
        self.server_name = server_name
        self.my_hand = []
        self.dealer_hand = []
        self.phase = Phase.P_INIT
        self.stats = {'wins': 0, 'losses': 0, 'ties': 0}
        self.rounds_played = 0
        self.total_rounds = 0

    def play(self):
        """Main game loop."""
        self.total_rounds = self._get_rounds()
        self.tcp_socket.sendall(request_Message(self.total_rounds, self.client_name))
        print(f"\nStarting game for {self.total_rounds} rounds\n")
        while True:
            try:
                # we set a 12 seconds timeout, if the server needs more than 12 seconds to send its payload message it probably means its disconnected or something
                # so we disable the connection and look for offers to play again.
                self.tcp_socket.settimeout(12.0)
                # buffer size is exactly 9 bytes becuase we know that the server payload message size is supposed to be 9 bytes in size.
                data = recv_exact(self.tcp_socket, 9)
            except (socket.timeout, ConnectionError):
                print("Connection lost. Returning to offer listening.")
                return
            # in case of a corrupt packet we make sure that the data is not "None"
            parsed = unpack_server_payload(data)
            if not parsed:
                continue
            result, rank, suit = parsed
            card = self._format_card(rank, suit)
            self._handle_card_received(result, card)
            # if result  != 0 aka result != 0x0 means the round is over, we update the statistics and reset the game for the next round
            if result != 0:
                self._handle_round_end(result)
                if self.rounds_played == self.total_rounds:
                    print(
                        f'Finished playing {self.rounds_played} rounds, win rate: {self.stats["wins"] / self.total_rounds * 100:.1f}%')
                    self._display_final_stats()
                    return

    def _handle_card_received(self, result, card):
        """Process a card received from server based on current phase."""

        # display who drew the card
        if self.phase in (Phase.P_INIT, Phase.P_TURN):
            print(f'{self.client_name} drew {card}')
        else:
            print(f'{self.server_name} drew {card}')

        # if round is ongoing (result == 0)
        if result == 0:
            if self.phase == Phase.P_INIT:
                self.my_hand.append(card)
                # since its client turn and its the start of the game, i check if the client already received 2 cards
                # if yeah then its time for the dealer to receives his cards so i update the phase.
                if len(self.my_hand) == 2:
                    self.phase = Phase.D_UP
            # behind the scenes ( check ServerGameSession ) dealer already received his 2 cards but in client part
            # we only show the first card the dealer got
            elif self.phase == Phase.D_UP:
                self.dealer_hand.append(card)
                self._display_hands(hide_dealer_second=True)
                # after both client and dealer got their cards we ask the client if he wishes to stand or hit
                decision = self._get_decision()
                self._send_decision(decision)
                # we update the game phase according to his decision
                self.phase = Phase.P_TURN if decision == "1" else Phase.D_TURN
                if decision == "2":
                    print(f"\n--- Dealer's Turn ---")

            # if client chose to Hit then we add the new card to his hand, display both his and dealer hands then ask for hit or stand again
            elif self.phase == Phase.P_TURN:
                self.my_hand.append(card)
                self._display_hands(hide_dealer_second=True)
                decision = self._get_decision()
                self._send_decision(decision)
                if decision == "2":
                    self.phase = Phase.D_TURN
                    print(f"\n--- Dealer's Turn ---")
            # if client chose to stand then we show the dealer shows his hidden card and behind the scenes ( check ServerGameSession ) he receives another card.
            elif self.phase == Phase.D_TURN:
                self.dealer_hand.append(card)
                self._display_hands()
        else:  # a reminder that this 'else' belongs to the "if" that checks if the result is 0 meaning round isn't over.
            # since we got here means the dealer or the client busted ( or both of them are in between 17 and 21 )
            if self.phase in (Phase.P_INIT,Phase.P_TURN):  # if we are in client turn then the final card that ended the round belongs to the client
                self.my_hand.append(card)
            else:  # else means it belongs to the dealer
                self.dealer_hand.append(card)

    def _handle_round_end(self, result):
        """Handles end of round - update stats and display results."""
        self.rounds_played += 1
        self._update_stats(result)
        self._display_round_end(result)

        # reset everything for the next round
        self.my_hand = []
        self.dealer_hand = []
        self.phase = Phase.P_INIT

    def _format_card(self, rank, suit):
        """Convert rank and suit to readable card string."""
        card_suit, card_rank = decode_card(rank, suit)
        return f"{card_rank} of {card_suit}"

    def _send_decision(self, decision):
        """Send player's decision to server."""
        action = "Hittt" if decision == "1" else "Stand"
        self.tcp_socket.sendall(pack_Client_Payload(action))

    def _display_hands(self, hide_dealer_second=False):
        """Display current hands."""
        if hide_dealer_second and len(self.dealer_hand) > 1:
            dealer_display = [self.dealer_hand[0], "[Hidden]"]
        else:
            dealer_display = self.dealer_hand

        print(f'{self.client_name} hand: {self.my_hand}')
        print(f'{self.server_name} hand: {dealer_display}\n')

    def _update_stats(self, result):
        """Update statistics based on round result."""
        if result == 1:
            self.stats['ties'] += 1
        elif result == 2:
            self.stats['losses'] += 1
        else:
            self.stats['wins'] += 1

    def _display_round_end(self, result):
        """Display round end message and final hands."""
        if result == 1:
            print(f'\n---Round OVER: round ended in a tie.---')
        elif result == 2:
            print(f'\n---Round OVER: round ended in a loss.---')
        else:
            print(f'\n---Round OVER: round ended in a win.---')

        self._display_hands()

    def _display_final_stats(self):
        """Display final game statistics."""
        print(f"\n{'=' * 50}")
        print(f"GAME OVER: YOUR OVERALL STATISTICS AFTER {self.total_rounds} rounds")
        print(f"Wins: {self.stats['wins']} ({self.stats['wins'] / self.total_rounds * 100:.1f}%)")
        print(f"Losses: {self.stats['losses']} ({self.stats['losses'] / self.total_rounds * 100:.1f}%)")
        print(f"Ties: {self.stats['ties']} ({self.stats['ties'] / self.total_rounds * 100:.1f}%)")
        print(f"{'=' * 50}\n")

    def _get_decision(self):
        """Get player's hit or stand decision."""
        decision = input(f'Choose the number that matches your choice:\n'
                         f'1.Hit\n2.Stand\n')
        while decision not in {"1", "2"}:
            decision = input(f'Invalid choice please pick again:\n'
                             f'1.Hit\n2.Stand\n')
        return decision

    def _get_rounds(self):
        """Get number of rounds to play from user."""
        while True:
            rounds = input("How many rounds do you want to play?\n")
            try:
                rounds = int(rounds)
                if 1 <= rounds <= 255:
                    return rounds
                else:
                    print("Please enter a number between 1 and 255.")
            except ValueError:
                print("Invalid number, please try again.")