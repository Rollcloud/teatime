world = new Object();

world.maps = {
  'chess-board': {
    'filename': 'chess-board.png',
    'pixels': { 'x': 768, 'y': 768 },
    'grid': { 'x': 8, 'y': 8 }
  },
  'forest-glade': {
    'filename': 'forest-glade.png',
    'pixels': { 'x': 4200, 'y': 4200 },
    'grid': { 'x': 10, 'y': 10 }
  },
  'observatory-tea': {
    'filename': 'observatory-tea.png',
    'pixels': { 'x': 4736, 'y': 1536 },
    'grid': { 'x': 74, 'y': 24 }
  },
}

world.characters = {};

world.addCharacter = function(data) {
  world.characters[data.token] = data;
};

world.removeCharacter = function(token) {
  world.characters[token] = undefined;
};

world.commandMove = function(delta) {
  character = world.characters[delta.token]
  pos_x = character.pos_x + delta.x;
  pos_y = character.pos_y + delta.y;

  return !world.collides(pos_x, pos_y);
};

world.moveCharacter = function(data) {
  let character = document.getElementById(data.token);

  // calculate square size
  square_x = world.map.pixels.x / world.map.grid.x;
  square_y = world.map.pixels.y / world.map.grid.y;

  // update character in world model
  world.characters[data.token].pos_x = data.pos_x;
  world.characters[data.token].pos_y = data.pos_y;

  // position character in DOM
  character.style.left = square_x * data.pos_x + 'px';
  character.style.top = square_y * data.pos_y + 'px';
};

world.collides = function(x, y) {
  // check for map borders
  if (x < 0 || y < 0) return true;
  if (x >= world.map.grid.x || y >= world.map.grid.y) return true;

  // check for collisions with other characters
  for (const [token, character] of Object.entries(world.characters)) {
    if (character.pos_x == x && character.pos_y == y) return true;
  }

  return false;
};

world.createWorld = function(mapElement, mapName) {
  map = world.maps[mapName];
  world.map = map;

  // build map
  document.querySelector(mapElement).style.backgroundImage =
    `url('/static/maps/${map.filename}')`;
}
