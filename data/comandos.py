# data/commands.py

# ==============================================================================
# Lista de Comandos Esperados (COMMANDS)
# ==============================================================================
# Comandos esperados que um motor de jogo de FI clássico esperaria.
# A grande maioria segue o padrão do Zork I, de 1 ou 2 palavras (Verbo + Substantivo).

COMANDOS_ESPERADOS = [
    # --- Navegação ---
    "go north",
    "go south",
    "go east",
    "go west",
    "go up",
    "go down",
    "enter building",
    "exit building",
    "climb tree",
    "swim river",

    # --- Interação com ibjetos ---
    "take lamp",
    "drop lamp",
    "take key",
    "drop key",
    "take sword",
    "drop sword",
    "take all",
    "open door",
    "close door",
    "open chest",
    "close chest",
    "unlock door",
    "lock door",
    "unlock chest",
    "light torch",
    "extinguish torch",
    "read book",
    "read scroll",
    "push rock",
    "pull lever",
    "move rug",
    "eat bread",
    "drink water",
    "wear helmet",
    "remove helmet",

    # --- Ações de status ---
    "look",
    "inventory",
    "examine door",
    "examine key",
    "examine troll",
    "wait",
    "sleep",

    # --- Combate ---
    "attack troll",
    "kill troll",
    "flee",

    # --- Comunicação ---
    "talk guard",
    "give coin",
    "ask guard",
]

# ==============================================================================
# Dicionário de Consultas de Teste (TEST_QUERIES) - versão expandida
# ==============================================================================
ENTRADAS_DE_TESTE = {
    # --- GO / Navegação (go north, south, east, west, up, down) ---
    "move north": "go north",
    "walk north": "go north",
    "i want to go north": "go north",
    "n": "go north",
    "north": "go north",
    "go n": "go north",

    "move south": "go south",
    "head south": "go south",
    "go to the south": "go south",
    "s": "go south",
    "south": "go south",
    "go s": "go south",

    "move east": "go east",
    "i want to walk east": "go east",
    "walk to the east": "go east",
    "e": "go east",
    "east": "go east",
    "go e": "go east",

    "move west": "go west",
    "go towards the west": "go west",
    "head to the west": "go west",
    "w": "go west",
    "west": "go west",
    "go w": "go west",

    "go up": "go up",
    "climb up": "go up",
    "ascend": "go up",
    "climb the ladder": "go up",
    "climb the stairs": "go up",
    "u": "go up",

    "go down": "go down",
    "descend": "go down",
    "go downstairs": "go down",
    "descend the stairs": "go down",
    "d": "go down",
    "down": "go down",

    # --- entrar / sair (enter building, exit building) ---
    "go inside the house": "enter building",
    "enter the building": "enter building",
    "come inside": "enter building",
    "go in": "enter building",
    "step inside": "enter building",

    "leave the house": "exit building",
    "let's leave this place": "exit building",
    "go outside": "exit building",
    "exit the building": "exit building",
    "get out": "exit building",

    # --- climb tree / swim river ---
    "climb the tree": "climb tree",
    "climb tree": "climb tree",
    "go upp the treee": "climb tree",    # typo intended
    "climb the treee": "climb tree",     # typo intended
    "i want to climb the tree": "climb tree",

    "swim across the river": "swim river",
    "i will swim across the river": "swim river",
    "swim river": "swim river",
    "swim in the river": "swim river",

    # --- Objetos: take/drop lamp ---
    "take lamp": "take lamp",
    "pick up the lamp": "take lamp",
    "pick up the shiny lamp": "take lamp",
    "grab lantern": "take lamp",
    "grab the lamp": "take lamp",
    "get the lamp": "take lamp",

    "drop lamp": "drop lamp",
    "put down the lamp": "drop lamp",
    "leave the lamp here": "drop lamp",
    "drp lamp": "drop lamp",              # typo
    "put lamp down": "drop lamp",

    # --- take/drop key ---
    "take key": "take key",
    "get the key": "take key",
    "pick up the small key": "take key",
    "i need that key": "take key",

    "drop key": "drop key",
    "put down the key": "drop key",
    "i don't want this key": "drop key",
    "i dont need this key anymore": "drop key",

    # --- take/drop sword ---
    "take sword": "take sword",
    "grab the sword": "take sword",
    "get sword": "take sword",
    "i will take the sharp sword": "take sword",

    "drop sword": "drop sword",
    "put down my sword": "drop sword",
    "leave my sword on the ground": "drop sword",
    "drop my weapon": "drop sword",

    # --- take all / inventory-group ---
    "take all": "take all",
    "get everything": "take all",
    "grab everything": "take all",
    "pick up all the items": "take all",

    # --- open/close door / chest / unlock/lock ---
    "open door": "open door",
    "open the wooden door": "open door",
    "try opening the door": "open door",
    "open door with key": "open door",

    "close door": "close door",
    "shut the door": "close door",
    "i want to close the door": "close door",
    "clse the door": "close door",       # typo

    "open chest": "open chest",
    "open the treasure chest": "open chest",
    "try to open the chest": "open chest",

    "close chest": "close chest",
    "shut the chest": "close chest",
    "close the chest": "close chest",

    "unlock door": "unlock door",
    "use my key on the door": "unlock door",
    "use key on door": "unlock door",
    "unlock the door with the key": "unlock door",

    "lock door": "lock door",
    "lock the door with the iron key": "lock door",
    "please lock the door": "lock door",

    "unlock chest": "unlock chest",
    "unlock the chest with the key": "unlock chest",
    "use key on chest": "unlock chest",

    # --- light / extinguish torch ---
    "light torch": "light torch",
    "turn on the torch": "light torch",
    "ignite torch": "light torch",

    "extinguish torch": "extinguish torch",
    "put out the fire": "extinguish torch",
    "snuff out the torch": "extinguish torch",

    # --- read book / read scroll ---
    "read book": "read book",
    "look at the book": "read book",
    "i want to read the book": "read book",
    "open the book": "read book",

    "read scroll": "read scroll",
    "look at the scroll": "read scroll",
    "i want to read the ancient scroll": "read scroll",

    # --- push rock / pull lever / move rug ---
    "push rock": "push rock",
    "shove the big rock": "push rock",
    "push the rock aside": "push rock",

    "pull lever": "pull lever",
    "i should pull that lever": "pull lever",
    "pull the lever": "pull lever",

    "move rug": "move rug",
    "pull the rug": "move rug",
    "push the rug aside": "move rug",
    "look under the rug": "move rug",

    # --- eat / drink ---
    "eat bread": "eat bread",
    "eat some food": "eat bread",
    "i will eat the bread": "eat bread",

    "drink water": "drink water",
    "drink from the flask": "drink water",
    "take a sip of water": "drink water",

    # --- wear / remove helmet ---
    "wear helmet": "wear helmet",
    "put on the helmet": "wear helmet",
    "equip helmet": "wear helmet",

    "remove helmet": "remove helmet",
    "take off helmet": "remove helmet",
    "remove my helmet": "remove helmet",
    "take off the helmet": "remove helmet",

    # --- look / examine / inventory / status ---
    "look": "look",
    "look around the room": "look",
    "look around": "look",
    "examine room": "look",
    "search the room": "look",

    "inventory": "inventory",
    "what am i carrying?": "inventory",
    "check my items": "inventory",
    "i": "inventory",

    "examine door": "examine door",
    "inspect the wooden door": "examine door",
    "look at the door": "examine door",
    "what does the door look like?": "examine door",

    "examine key": "examine key",
    "examine the rusty key": "examine key",
    "inspect key": "examine key",

    "examine troll": "examine troll",
    "inspect the troll": "examine troll",
    "look at the troll": "examine troll",

    "wait": "wait",
    "i will wait for a moment": "wait",
    "please wait": "wait",

    "sleep": "sleep",
    "go to sleep now": "sleep",
    "rest for a while": "sleep",

    # --- combate: attack / kill / flee ---
    "attack troll": "attack troll",
    "fight the troll with my sword": "attack troll",
    "strike the troll": "attack troll",
    "hit the troll": "attack troll",
    "engage the troll": "attack troll",

    "kill troll": "kill troll",
    "slay the ugly troll": "kill troll",
    "finish the troll": "kill troll",
    "destroy the monster": "kill troll",

    "flee": "flee",
    "run away!": "flee",
    "escape from battle": "flee",
    "get out of here": "flee",

    # --- comunicação: talk / give / ask ---
    "talk guard": "talk guard",
    "speak to the guard": "talk guard",
    "talk with the guard": "talk guard",
    "have a word with the guard": "talk guard",

    "give coin": "give coin",
    "i give the guard a coin": "give coin",
    "offer money to the guard": "give coin",
    "give the guard a coin": "give coin",

    "ask guard": "ask guard",
    "ask about the key": "ask guard",
    "ask the guard where the key is": "ask guard",
    "question the guard": "ask guard",

    # --- extras / abreviações e typos variados ---
    "open chest with key": "open chest",
    "open the chest with the key": "open chest",
    "unlocking chest": "unlock chest",
    "take everything": "take all",
    "grab all": "take all",
    "pick everything up": "take all",

    "drop everything": "drop lamp",   # caso limite: mapeado para drop lamp (ajustável)
    "leave everything": "drop lamp",

    "shut door": "close door",
    "shut the wooden door": "close door",

    "light the torch": "light torch",
    "turn torch on": "light torch",
    "turn the torch on": "light torch",

    "extinguish the torch": "extinguish torch",
    "put out torch": "extinguish torch",

    "look book": "read book",
    "read the book": "read book",

    "drink flask": "drink water",
    "sip water": "drink water",

    # --- intentionally tricky paraphrases ---
    "i will go northeast": "go north",
    "can i go north?": "go north",
    "i want to head west": "go west",
    "i am going to climb that tree": "climb tree",
    "i'm going to swim the river": "swim river",

    # --- short/fragmented inputs ---
    "open": "open door",   # escolha de fallback para teste (ajustável)
    "close": "close door",
    "take": "take lamp",
    "drop": "drop lamp",
    "read": "read book",
    "use key": "unlock door",

    # --- more typos / contractions ---
    "go nort": "go north",
    "go wes": "go west",
    "climb ladder": "go up",
    "climb ladde": "go up",
    "drp the lamp": "drop lamp",
    "piick up lamp": "take lamp",

    # --- pragmatic / polite forms ---
    "please open the door": "open door",
    "could you open the chest?": "open chest",
    "please give coin to guard": "give coin",

    # --- test ambiguity resolution (mapped to a chosen canonical) ---
    "look at the lamp": "read book",   # deliberately ambiguous (test how system handles)
    "inspect the lamp": "read book",

    # --- filler / nonsense to test rejection (map to close command as placeholder) ---
    "sing to the troll": "talk guard",  # mapped as a communication attempt (test robustness)
    "dance by the river": "swim river", # mapped arbitrarily for stress-testing
    "look lamp": "drop lamp"
    

    # End of expanded test queries
}
