from itertools import combinations
import random
import copy


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        From the spex: Any time the number of cells is equal to the count,
        we know that all of that sentence’s cells must be mines.
        """
        return self.cells if len(self.cells) == self.count else None

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        From the spex: any time we have a sentence whose count is 0, 
        we know that all of that sentence’s cells must be safe.
        """
        return self.cells if self.count == 0 else None

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            trans = copy.deepcopy(self.cells)
            trans.discard(cell)
            self.cells = trans
            self.count -= 1

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            trans = copy.deepcopy(self.cells)
            trans.discard(cell)
            self.cells = trans


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

        # A change marker to knowledge
        self.KB_has_changed = False

        # the empty sentence
        self.empty = Sentence(set(), 0)

        # the list of all possible moves on the grid
        self.all_possible_moves = self.all_possible_moves()

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        if cell not in self.mines:
            self.mines.add(cell)
            self.KB_has_changed = True
            for s in self.knowledge:
                Sentence.mark_mine(s, cell)
        else:
             self.KB_has_changed = False

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        if cell not in self.mines:
            self.safes.add(cell)
            self.KB_has_changed = True
            for s in self.knowledge:
                Sentence.mark_safe(s, cell)
        else:
             self.KB_has_changed = False

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.
        """
        """
        1) mark the cell as a move that has been made
        """
        self.moves_made.add(cell)

        """
        2) mark the cell as safe
        """
        self.mark_safe(cell)

        """ 
        3) add a new sentence to the AI's knowledge base
           based on the value of `cell` and `count`
           From spex: only include neigbouring'cells whose state 
           is still undetermined ie. neither known mines nor known safes
        """
        self.add_new_sentence(cell, count)

        """
        4) mark any additional cells as safe or as mines
           if it can be concluded based on the AI's knowledge base
        """
        self.mark_additional_cells()

        """
        5) add any new sentences to the AI's knowledge base
        if they can be inferred from existing knowledge
        """
        self.add_inferred_sentence()

        """
        6) Loops marking additional cells and infering new sentences
        """
        # Has the knowledge changed since our new sentence inclusion?
        while self.KB_has_changed:
            self.KB_has_changed = False
            self.mark_additional_cells()
            self.add_inferred_sentence()

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        safe_moves = self.safes - self.moves_made
        if len(safe_moves) > 0:
            return safe_moves.pop()
        else:
            return None

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        random_move = self.all_possible_moves - self.moves_made - self.mines

        if len(random_move) > 0:
            return random_move.pop()
        else:
            return None

    """ 
    ========================================================================
    ------------------------------  UTILITY --------------------------------
    ======================================================================== 
    """

    """
    -------------------------------------------------------------------------------
    3a) Takes a cell and a count, find all neighbours, only keep undetermined ones,
    adjust count, creates a new sentence and adds it to knowledge
    -------------------------------------------------------------------------------
    """

    def add_new_sentence(self, cell, count):

        # get all neighbors omitting cell itself
        neighbors = self.neighbors(cell)

        # creates a new sentence by removing known safes and mines
        # marks potential new found mines and safes, and updates knowledge base
        sentence = self.clean_up(neighbors, count)

        # add sentence to knowledge only if sentence is not none and not already known
        if sentence:
            self.add_if_new(sentence)

    """
    3b) Adds new sentence to knowledge if not empty or already there
    """

    def add_if_new(self, sentence):
        if len(self.knowledge) == 0:
            self.KB_has_changed = True
            self.knowledge.append(sentence)
        elif not self.in_knowledge(sentence):
            self.KB_has_changed = True
            self.knowledge.append(sentence)

    """
    3c) Append sentence to knowledge if not already present
    """

    def in_knowledge(self, sentence):
        return any(list(filter(lambda s: sentence.__eq__(s), self.knowledge)))

    """
    ---------------------------------------------
    4a) Check knowledge for any new mines or safes
    ---------------------------------------------
    """

    def mark_additional_cells(self):
        for s in self.knowledge:
            new_mines = Sentence.known_mines(s)
            new_safes = Sentence.known_safes(s)
            if new_mines:
                self.KB_has_changed = True
                self.mark_mines(new_mines)
            elif new_safes:  # and new safes
                self.KB_has_changed = True
                self.mark_safes(new_safes)

    """
    ----------------------------
    4b) Marks all cells as safes
    ----------------------------
    """

    def mark_safes(self, new_safes):
        for a in new_safes:
            if a not in self.safes:
                self.mark_safe(a)

    """
    4c) Marks all cells as mines
    """

    def mark_mines(self, new_mines):
        for m in new_mines:
            if m not in self.mines:  # we found new unlisted mines
                self.mark_mine(m)

    """
    -----------------------------------------------------------------------
    5a) Infers new knowledge based on set of cells inclusion into other set
    ----------------------------------------------------------------------- 
    """

    def add_inferred_sentence(self):
        pairs = self.unique_pairs()
        if pairs:
            for (s1, s2) in pairs:
                # adds knowledfge if s1 is a proper subset of s2
                if s1.cells < s2.cells:
                    cells = s2.cells - s1.cells
                    count = s2.count - s1.count
                    # sent1 = Sentence(cells, count)
                    sent1 = self.clean_up(cells, count)
                    # self.KB_has_changed = True
                    self.add_if_new(sent1)
                # or vice versa
                elif s2.cells < s1.cells:
                    cells = s1.cells - s2.cells
                    count = s1.count - s2.count
                    # sent2 = Sentence(cells, count)
                    sent2 = self.clean_up(cells, count)
                    # self.KB_has_changed = True
                    self.add_if_new(sent2)

    """
    ----------------------------------------------
    5b) finds unique pairs of sentences amongst KB
    ----------------------------------------------
    """

    def unique_pairs(self):
        return [(s1, s2) for s1, s2
                in combinations(filter(lambda s: self.is_not_empty(s), self.knowledge), 2)
                if not self.are_identicals(s1, s2)]

    """
    ==============================
    GENERAL MULTIPURPOSE UTILITIES
    ==============================
    """
    
    def are_identicals(self, s1, s2):
        return s1.__eq__(s2)

    def is_not_empty(self, s):
        return not s.__eq__(self.empty)

    def neighbors(self, cell):
        neighbors = set()
        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    neighbors.add((i, j))
        return neighbors


    """
    return sentence only including cells whose state is still undetermined
    """

    def clean_up(self, cells, count):
        # Remove known safes and mines
        trans_cells = copy.deepcopy(cells)
        for c in cells:
            if c in self.safes:
                trans_cells.discard(c)
            elif c in self.mines:
                trans_cells.discard(c)
                count -= 1
        # search for new safes and mines
        # update sets and knowledge
        if trans_cells:
            if count == 0:
                self.mark_safes(trans_cells)
                return None
            elif len(trans_cells) == count:
                self.mark_mines(trans_cells)
                return None
            else:
                return Sentence(trans_cells, count)
        return None

   
    def all_possible_moves(self):
        all_moves = set()
        for i in range(self.height):
            for j in range(self.width):
                all_moves.add((i, j))
        return all_moves
