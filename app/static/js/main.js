let socket;
let myToken;
let message_num = 0;
let past_messages = [];
let model = {
  'users': [],
};
let dirClasses = ['dir-N', 'dir-E', 'dir-S', 'dir-W'];
let volumeClasses = ['volume-one', 'volume-group', 'volume-all'];

function addUser(user) {
  // add to model
  model.users.push(user.token);

  // add to world
  world.addCharacter(user);

  // create user's character
  let character = stringToHTML(
    `
    <div class="character" id="${user.token}">
        <span class="character-direction"></span>
        <span class="character-avatar avatar">${user.avatar}</span>
        <span class="character-name">${user.name}</span>
    </div>
  `
  );
  character.style.left = '-100px';
  character.style.top = '-100px';

  document.querySelector('.world-characters').append(character);
  world.moveCharacter(user);
}

function removeUser(token) {
  // remove user's character
  let elem = document.getElementById(token);
  if (elem != null) {
    elem.parentNode.removeChild(elem);
  }
  // remove from world
  world.removeCharacter(token);

  // remove from model
  model.users = model.users.filter(e => e !== token)
}

function withinRange(you, me) {
  let dx = you.pos_x - me.pos_x;
  let dy = you.pos_y - me.pos_y;
  let distance = Math.hypot(dx, dy);
  let direction_to = calcAngleDegrees(dy, dx);
  let direction_delta = Math.abs(direction_to - me.direction);
  direction_delta = direction_delta > 180 ? 360 - direction_delta : direction_delta; // reduce to acute angle
  let threshold_distance, threshold_direction;
  switch (me.volume) {
    case "all":
      return true;
      break;
    case "group":
      threshold_distance = 2 * 1.42;
      threshold_direction = 90;
      break;
    case "one":
      threshold_distance = 1.0;
      threshold_direction = 0;
      break;
  }
  if (distance == 0 || (distance <= threshold_distance &&
      direction_delta <= threshold_direction))
    return true;
  return false;
}

function getCharactersNearby(token) {
  let nearby = [];
  let me = world.characters[token];

  // for character in world.characters
  for (const [yourToken, you] of Object.entries(world.characters)) {
    if (withinRange(you, me)) nearby.push(yourToken);
  }

  return nearby;
}

function writeToChat(text) {
  $('.chat-box').html($('.chat-box').html() + text + '<br>');
  $('.chat-box').scrollTop($('.chat-box')[0].scrollHeight);
}

function sendMovement(vertical, horizontal) {
  let delta = {
    'token': myToken,
    'x': horizontal,
    'y': vertical
  };
  let newDirection = calcAngleDegrees(vertical, horizontal);

  // * First rotate character, then move
  // if character is facing the movement direction
  if (world.characters[myToken].direction == newDirection) {
    // move character
    if (world.checkMove(delta)) {
      let data = world.getCharacterData(delta);
      world.moveCharacter(data);
      world.moveCamera(data);

      socket.emit('move', delta);
    }
  } else {
    // face new direction
    let characterDirection = document.getElementById(myToken).querySelector(
      '.character-direction');
    // get new direction class
    let newDirClass = dirClasses[newDirection / 90];
    characterDirection.classList.remove(...dirClasses);
    characterDirection.classList.add(newDirClass);
    // update character direction
    world.characters[myToken].direction = newDirection;
  }
}

$(document).ready(function() {
  // build map
  world.createWorld('.world', 'forest-glade'); // 'observatory-tea');

  var protocol = window.location.protocol;
  socket = io.connect(protocol + '//' + document.domain + ':' +
    location.port + '/chat');

  socket.on('user_joined', function(data) {
    let user = data.user;

    if (model.users.includes(user.token))
      removeUser(user.token);

    addUser(user);
    if (user.token == myToken) {
      world.characters[myToken].direction = 0;
      world.characters[myToken].volume = 'group';

      // add touch response to my character
      let touchArea = document.getElementById(myToken);
      let activeRegion = new ZingTouch.Region(touchArea);

      activeRegion.bind(touchArea, 'pan', event => {
        let gridSize = world.map.pixels.x / world.map.grid.x;
        let distance = Math.round(event.detail.data[0].distanceFromOrigin / gridSize);
        let direction = (90 - event.detail.data[0].directionFromOrigin +
          360) % 360;
        let down = Math.round(-1 * Math.cos(degToRad(direction)));
        let right = Math.round(Math.sin(degToRad(direction)));

        // attemp to move one block for every square gestured
        for (var i = gridSize; i > 0; i--) {
          sendMovement(down, right); // down, right - positive
        }
      });

      // make my direction-box visible
      document.getElementById(myToken).querySelector('.character-direction').style
        .visibility = 'visible';

      // position camera
      world.moveCamera(user);
      // remove loading screen
      // document.querySelector('.loadscreen .mdl-spinner').classList.remove('is-active');
      document.querySelector('.loadscreen').classList.add('success');
    }

  });

  socket.on('user_left', function(data) {
    let user = data.user;
    removeUser(user.token);
  });

  socket.on('disconnect', () => {
    for (var i = model.users.length - 1; i >= 0; i--) {
      if (model.users[i] !== myToken)
        removeUser(model.users[i]);
    }
  });

  socket.on('identify', function(data) {
    myToken = data.token;
  });

  socket.on('move', function(data) {
    world.moveCharacter(data);
    if (data.token == myToken)
      world.moveCamera(data);
  });

  socket.on('message', function(data) {
    writeToChat(`${data.handle}: <${data.volume}>${data.msg}</${data.volume}>`);
  });

  socket.on('status', function(data) {
    writeToChat(data.msg);
  });

  document.querySelector('.chat-bar').addEventListener('click', event => {
    $('#chat-input').focus();
  });

  // Volume buttons
  document.getElementById('volume-all').addEventListener('click', event => {
    world.characters[myToken].volume = 'all';
    let characterDirection = document.getElementById(myToken)
      .querySelector('.character-direction');
    characterDirection.classList.remove(...volumeClasses);
    characterDirection.classList.add(volumeClasses[2]);
    document.getElementById('volume-button').textContent = 'volume_up';
  });
  document.getElementById('volume-group').addEventListener('click', event => {
    world.characters[myToken].volume = 'group';
    let characterDirection = document.getElementById(myToken)
      .querySelector('.character-direction');
    characterDirection.classList.remove(...volumeClasses);
    characterDirection.classList.add(volumeClasses[1]);
    document.getElementById('volume-button').textContent = 'volume_down';
  });
  document.getElementById('volume-one').addEventListener('click', event => {
    world.characters[myToken].volume = 'one';
    let characterDirection = document.getElementById(myToken)
      .querySelector('.character-direction');
    characterDirection.classList.remove(...volumeClasses);
    characterDirection.classList.add(volumeClasses[0]);
    document.getElementById('volume-button').textContent = 'volume_mute';
  });

  let lastDown = 0;
  document.addEventListener('keydown', event => {
    const key = event.key; // "Enter", "ArrowRight", "ArrowLeft", "ArrowUp", or "ArrowDown"

    if (document.querySelector('#chat-input') === document.activeElement) {
      // if chat box is active
      switch (key) {

        case "Enter":
          text = $('#chat-input').val();
          $('#chat-input').val('');
          past_messages.unshift(text);
          users = getCharactersNearby(myToken);
          socket.emit('text', {
            msg: text,
            to: users,
            volume: world.characters[myToken].volume,
          });
          message_num = 0
          break;

        case "ArrowUp":
          $('#chat-input').val(past_messages[message_num]);
          message_num += 1
          break;

        case "ArrowDown":
          message_num -= 1
          $('#chat-input').val(past_messages[message_num]);
          break;
      }

    } else {
      // if map is active

      // each movement is animated for 0.15s
      // check if previous event still processing before triggering again
      let now = Date.now();

      if (now > lastDown + 125) { // check timout in milliseconds
        switch (key) {
          case "ArrowLeft":
            sendMovement(0, -1);
            lastDown = now;
            break;
          case "ArrowRight":
            sendMovement(0, 1);
            lastDown = now;
            break;
          case "ArrowUp":
            sendMovement(-1, 0);
            lastDown = now;
            break;
          case "ArrowDown":
            sendMovement(1, 0);
            lastDown = now;
            break;
        }
      }

    }

  });

});
