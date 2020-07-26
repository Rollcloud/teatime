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

  // create user's character
  let character = stringToHTML(
    `
    <div class="character" id="${user.token}">
      <span class="mdl-chip mdl-chip--contact">
        <span class="mdl-chip__contact mdl-color--indigo-50">${user.avatar}</span>
        <span class="mdl-chip__text">${user.name}</span>
      </span>
    </div>
  `
  );
  character.style.left = 30 * user.pos_x + 'px';
  character.style.top = 30 * user.pos_y + 'px';

  document.querySelector('.map-users').append(character);
}

function removeUser(token) {
  // remove user's character
  let elem = document.getElementById(token);
  if (elem != null) {
    elem.parentNode.removeChild(elem);
  }

  // remove from model
  model.users = model.users.filter(e => e !== token)
}

function writeToChat(text) {
  $('.chat-box').html($('.chat-box').html() + text + '<br>');
  $('.chat-box').scrollTop($('.chat-box')[0].scrollHeight);
}

function moveCharacter(vertical, horizontal) {
  socket.emit('move', {
    'token': myToken,
    'vertical': vertical,
    'horizontal': horizontal
  });
}

$(document).ready(function() {
  socket = io.connect('http://' + document.domain + ':' +
    location.port + '/chat');

  socket.on('user_joined', function(data) {
    let user = data['user'];

    if (model.users.includes(user.token))
      removeUser(user.token);

    addUser(user);
  });

  socket.on('user_left', function(data) {
    let user = data['user'];
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
    let character = document.getElementById(data.token);
    character.style.left = 30 * data.pos_x + 'px';
    character.style.top = 30 * data.pos_y + 'px';
  });

  socket.on('message', function(data) {
    writeToChat(data.msg);
  });

  document.addEventListener('keydown', event => {
    const key = event.key; // "ArrowRight", "ArrowLeft", "ArrowUp", or "ArrowDown"
    switch (key) {
      case "ArrowLeft":
        moveCharacter(0, -1);
        break;
      case "ArrowRight":
        moveCharacter(0, 1);
        break;
      case "ArrowUp":
        moveCharacter(-1, 0);
        break;
      case "ArrowDown":
        moveCharacter(1, 0);
        break;
    }
  });

  document.querySelector('#chat-input').addEventListener('keyup', event => {
    let code = event.keyCode || event.which;
    if (code == 13) { // enter
      text = $('#chat-input').val();
      $('#chat-input').val('');
      past_messages.unshift(text);
      socket.emit('text', { msg: text });
      message_num = 0

    } else if (code == 38) { // up-arrow
      $('#chat-input').val(past_messages[message_num]);
      message_num += 1

    } else if (code == 39) { // down-arrow
      message_num -= 1
      $('#chat-input').val(past_messages[message_num]);
    }
  });

});
