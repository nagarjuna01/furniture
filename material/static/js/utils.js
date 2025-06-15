// utils.js
function showAlert(msg) {
  alert(msg);
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function setupEnableDisable(selectId, editBtnId, deleteBtnId) {
  const select = document.getElementById(selectId);
  const editBtn = document.getElementById(editBtnId);
  const deleteBtn = document.getElementById(deleteBtnId);

  editBtn.disabled = true;
  deleteBtn.disabled = true;

  select.addEventListener('change', () => {
    const hasValue = !!select.value;
    editBtn.disabled = !hasValue;
    deleteBtn.disabled = !hasValue;
    editBtn.classList.toggle('active', hasValue);
    deleteBtn.classList.toggle('active', hasValue);
  });
}
