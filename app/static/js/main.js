let socket;
let myToken;
let message_num = 0;
let past_messages = [];
let model = {
  'users': [],
};

function addUser(user) {
  // add to model
  model.users.push(user.token);

  // add to world
  world.addCharacter(user);

  // create user's character
  let character = stringToHTML(
    `
    <div class="character" id="${user.token}">
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

function writeToChat(text) {
  $('.chat-box').html($('.chat-box').html() + text + '<br>');
  $('.chat-box').scrollTop($('.chat-box')[0].scrollHeight);
}

function sendMovement(vertical, horizontal) {
  delta = {
    'token': myToken,
    'x': horizontal,
    'y': vertical
  };
  if (world.checkMove(delta)) {
    let data = world.getCharacterData(delta);
    world.moveCharacter(data);
    world.moveCamera(data);

    socket.emit('move', delta);
  }
}

$(document).ready(function() {
  // build map
  world.createWorld('.world', 'forest-glade'); // 'observatory-tea');

  socket = io.connect('http://' + document.domain + ':' +
    location.port + '/chat');

  socket.on('user_joined', function(data) {
    let user = data.user;

    if (model.users.includes(user.token))
      removeUser(user.token);

    addUser(user);
    if (user.token == myToken) {
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
    writeToChat(data.handle + ": " + data.msg);
  });

  socket.on('status', function(data) {
    writeToChat(data.msg);
  });

  document.querySelector('.chat-bar').addEventListener('click', event => {
    $('#chat-input').focus();
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
          socket.emit('text', { msg: text });
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
