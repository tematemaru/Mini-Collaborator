const crypto = require('crypto');

function sha256(password) {
  return crypto
    .createHash('sha256')
    .update(password, 'utf8')
    .digest('hex');
}

// пример
const password = "Administrator";
console.log(sha256(password));