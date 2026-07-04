import random
from playcard import make_deck

CARD_VALUES = {
    'A': 11,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    'T': 10,
    'J': 10,
    'Q': 10,
    'K': 10,
}

def calculate_hand_value(hand):
    value, aces = 0, 0
    for card in hand:
        rank = card[0]
        value += CARD_VALUES[rank]
        aces += rank == 'A'
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

# 新增：判断是否天然黑杰克（两张牌A+10）
def is_natural_blackjack(hand):
    if len(hand) != 2:
        return False
    ranks = [c[0] for c in hand]
    if 'A' in ranks:
        other = ranks[0] if ranks[1] == 'A' else ranks[1]
        return other in ('T', 'J', 'Q', 'K')
    return False

def new_game(session):
    session_id = session.get('session_id', '')
    deck = make_deck()
    random.shuffle(deck)
    # 抽牌：玩家1、庄家明牌、玩家2、庄家暗牌
    p1, d_open, p2, d_hidden = deck.pop(), deck.pop(), deck.pop(), deck.pop()
    player_hand = [p1, p2]
    dealer_hand = [d_open]

    dealer_value = calculate_hand_value(dealer_hand)
    player_value = calculate_hand_value(player_hand)

    # 欧式规则：开局不检查庄家黑杰克
    message = None
    message_class = ""

    session['game_state'] = {
        'deck': deck,
        'dealer_hand': dealer_hand,
        'dealer_hidden': d_hidden,  # 单独存储庄家暗牌
        'player_hand': player_hand,
        'dealer_value': dealer_value,
        'player_value': player_value,
        'message': message,
        'message_class': message_class,
    }

def game_update(session, action):
    game_state = session.get('game_state', {})
    if not game_state:
        return new_game(session)
    deck = game_state['deck']
    dealer_hand = game_state['dealer_hand']
    player_hand = game_state['player_hand']

    if action == 'hit':
        card = deck.pop()
        player_hand.append(card)
        player_value = calculate_hand_value(player_hand)
        game_state['player_value'] = player_value
        if player_value > 21:
            game_state['dealer_value'] = calculate_hand_value(dealer_hand)
            game_state['message'] = 'You busted! Dealer wins.'
            game_state['message_class'] = 'lose-message'
    elif action == 'stand':
        player_value = game_state['player_value']
        # 亮出庄家暗牌，合并进手牌
        hidden_card = game_state['dealer_hidden']
        dealer_hand.append(hidden_card)
        dealer_natural = is_natural_blackjack(dealer_hand)
        player_natural = is_natural_blackjack(player_hand)

        if dealer_natural:
            # 庄家天然黑杰克特殊判定
            if player_natural:
                game_state['message'] = "It's a tie of double blackjack!"
                game_state['message_class'] = "tie-message"
            else:
                game_state['message'] = "Dealer wins with natural blackjack!"
                game_state['message_class'] = "lose-message"
            game_state['dealer_value'] = calculate_hand_value(dealer_hand)
        else:
            # 庄家无BJ，执行补牌
            dealer_value = calculate_hand_value(dealer_hand)
            while dealer_value < 17:
                new_card = deck.pop()
                dealer_hand.append(new_card)
                dealer_value = calculate_hand_value(dealer_hand)
            game_state['dealer_value'] = dealer_value
            # 常规胜负
            if dealer_value > 21:
                game_state['message'] = 'Dealer busted! You win!'
                game_state['message_class'] = 'win-message'
            elif dealer_value > player_value:
                game_state['message'] = 'Dealer wins!'
                game_state['message_class'] = 'lose-message'
            elif dealer_value < player_value:
                game_state['message'] = 'You win!'
                game_state['message_class'] = 'win-message'
            else:
                game_state['message'] = "It's a tie!"
    session.modified = True