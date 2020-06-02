function validateNewGridForm() {
  n = document.forms["ng-form"]["n"].value;
  if (isNaN(n)) {
    alert(n + " is not a number");
    return false;
  }
  n = Number(n);
  if (n % 2 == 0) {
    alert(n + " is not an odd number")
    return false;
  }
  return true;
}
