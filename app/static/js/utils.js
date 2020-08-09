var support = (function() {
  if (!window.DOMParser) return false;
  var parser = new DOMParser();
  try {
    parser.parseFromString('x', 'text/html');
  } catch (err) {
    return false;
  }
  return true;
})();

/**
 * Convert a template string into HTML DOM nodes
 * @param  {String} str The template string
 * @return {Node}       The template HTML
 */
var stringToHTML = function(str) {
  // If DOMParser is supported, use it
  if (support) {
    var parser = new DOMParser();
    var doc = parser.parseFromString(str, 'text/html');
    return doc.body.firstChild;
  }

  // Otherwise, fallback to old-school method
  var dom = document.createElement('div');
  dom.innerHTML = str;
  return dom;
};

const loadJSON = (url, callback) => {
  let xobj = new XMLHttpRequest();
  xobj.overrideMimeType("application/json");
  xobj.open('GET', url, true);
  xobj.onreadystatechange = () => {
    if (xobj.readyState === 4 && xobj.status === 200) {
      // Required use of an anonymous callback
      // as .open() will NOT return a value but simply returns undefined in asynchronous mode
      callback(xobj.responseText);
    }
  };
  xobj.send(null);
}

function calcAngleDegrees(x, y) {
  return (Math.atan2(y, -x) * 180 / Math.PI + 360) % 360;
}

function degToRad(degrees) {
  return degrees * (Math.PI / 180);
};
