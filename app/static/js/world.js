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
    'grid': { 'x': 30, 'y': 30 }
  },
  'observatory-tea': {
    'filename': 'observatory-tea.png',
    'pixels': { 'x': 4736, 'y': 1536 },
    'grid': { 'x': 74, 'y': 24 },
    'json': 'Observatory_Tea.json'
  },
}

world.characters = {};

world.addCharacter = function(data) {
  world.characters[data.token] = data;
};

world.removeCharacter = function(token) {
  world.characters[token] = undefined;
};

world.checkMove = function(delta) {
  character = world.characters[delta.token]
  pos_x = character.pos_x + delta.x;
  pos_y = character.pos_y + delta.y;

  return !world.collides(pos_x, pos_y);
};

world.getCharacterData = function(delta) {
  let data = {
    'token': myToken,
    'pos_x': character.pos_x + delta.x,
    'pos_y': character.pos_y + delta.y
  };

  return data;
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
  character.style.left = (square_x / 2) + square_x * data.pos_x + 'px';
  character.style.top = (square_y / 2) + square_y * data.pos_y + 'px';
};

world.moveCamera = function(data) {
  let camera = world.camera;

  // calculate square size
  square_x = world.map.pixels.x / world.map.grid.x;
  square_y = world.map.pixels.y / world.map.grid.y;

  // update camera in world model
  world.camera.x = -square_x * data.pos_x;
  world.camera.y = -square_y * data.pos_y;

  world.updateCamera();
};

world.updateCamera = function() {
  let camera = world.camera;
  let cameraElement = document.querySelector('.world-camera');

  // calculate square size
  square_x = world.map.pixels.x / world.map.grid.x;
  square_y = world.map.pixels.y / world.map.grid.y;

  // calculate mid-point
  half_width = camera.width / 2;
  half_height = camera.height / 2;

  // calculate center map position
  map_left = camera.x + half_width;
  map_top = camera.y + half_height;

  // prevent over-scrolling of map edges
  map_left = Math.min(0, Math.max(map_left, -world.map.pixels.x + camera.width));
  map_top = Math.min(0, Math.max(map_top, -world.map.pixels.y + camera.height));

  // position camera in DOM
  cameraElement.style.left = map_left + 'px';
  cameraElement.style.top = map_top + 'px';
};

world.collides = function(x, y) {
  // check for map borders
  if (x < 0 || y < 0) return true;
  if (x >= world.map.grid.x || y >= world.map.grid.y) return true;

  // check for map obsticals
  if (map.hasOwnProperty('json')) {
    square_num = y * world.map.grid.x + x;
    for (var i = world.map.collisions.length - 1; i >= 0; i--) {
      if (square_num == world.map.collisions[i])
        return true;
    }
  }

  // check for collisions with other characters
  for (const [token, character] of Object.entries(world.characters)) {
    if (character.pos_x == x && character.pos_y == y) return true;
  }

  return false;
};

world.createWorld = function(worldElement, mapName) {
  // load map
  map = world.maps[mapName];
  world.map = map;

  // load collisions
  if (map.hasOwnProperty('json')) {
    loadJSON('/static/maps/' + map.json, (response) => {
      // Parse JSON string into object
      let jsonMap = JSON.parse(response);
      map.collisions = [];
      for (var i = jsonMap.collisions.length - 1; i >= 0; i--) {
        map.collisions.push(jsonMap.collisions[i].split(':')[0]);
      }
    });
  }
  // create DOM
  let worldContainer = document.querySelector(worldElement);

  let worldCamera = document.createElement('div');
  worldCamera.classList.add('world-camera')
  worldContainer.appendChild(worldCamera);

  let worldMap = document.createElement('div');
  worldMap.classList.add('world-map')
  worldCamera.appendChild(worldMap);

  let worldCharacters = document.createElement('div');
  worldCharacters.classList.add('world-characters')
  worldCamera.appendChild(worldCharacters);

  // build map
  worldMap.style.backgroundImage = `url('/static/maps/${map.filename}')`;
  worldMap.style.width = map.pixels.x + 'px';
  worldMap.style.height = map.pixels.y + 'px';

  // create camera
  world.camera = new Object();
  world.camera.x = 0;
  world.camera.y = 0;
  world.camera.width = worldContainer.getBoundingClientRect().width;
  world.camera.height = worldContainer.getBoundingClientRect().height;

  // detect window szie changes and update camera
  window.addEventListener('resize', function() {
    let camera = world.camera;

    camera.width = worldContainer.getBoundingClientRect().width;
    camera.height = worldContainer.getBoundingClientRect().height;

    world.updateCamera();
  });

  // finally, draw world
  world.updateCamera();
}
