board = [
 ['r','n','b','m','k','b','n','r'],
 ['.','.','.','.','.','.','.','.'],
 ['p','p','p','p','p','p','p','p'],
 ['.','.','.','.','.','.','.','.'],
 ['.','.','.','.','.','.','.','.'],
 ['P','P','P','P','P','P','P','P'],
 ['.','.','.','.','.','.','.','.'],
 ['R','N','B','K','M','B','N','R']
]


buttons = []
selected = None
turn = 0



def on_click(r, c):
    global selected
    global turn

    if selected is None:
        if board[r][c] != '.' and check_turn(board[r][c],turn)  :
            selected = (r, c)
    else:
        a,b = selected
        if check_legal_move(board[a][b],selected, (r, c)) :
                move_piece(selected, (r, c))
                selected = None
                turn = 1 - turn
                update_board()
        else :
            selected = None
            print("illegal move")


def get_board():
    return board

def check_legal_move(piece,start,end):

    if start == end :
        return False

    sr, sc = start
    er, ec = end

    if piece.lower() == 'p' :
        column = sc - ec 
        if column != 0 :
            return False
        return True
    



def check_turn(piece,turn):
    if piece.islower() and turn == 1 :
        return True
    if piece.isupper() and turn == 0 :
        return True
    return False

def move_piece(start, end):
    sr, sc = start
    er, ec = end


    board[er][ec] = board[sr][sc]
    board[sr][sc] = '.'


    



def update_board():
    for i in range(8):
        for j in range(8):
            buttons[i][j]['text'] = board[i][j]


def get_buttons():
    return buttons
