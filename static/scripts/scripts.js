$(document).ready(function(){
	$(document).on("click", ".selectable", function(e){
		var elem = $(this);
		if (e.shiftKey){
			elem.toggleClass("selected");

		}else{
      bool = elem.hasClass("selected");
      $(".selected").toggleClass("selected");
      if (!bool)
        elem.toggleClass("selected");
    }
	});

});

function toggleForm(id){
  $(id).toggle();
}

function openForm(id) {
  document.getElementById(id).style.display = "block";
}

function closeForm(id) {
  document.getElementById(id).style.display = "none";
}

function selectTags(select)
{
  var $ul = $(select).prev('ul');
   
  if ($ul.find('input[value=' + $(select).val() + ']').length == 0)
    $ul.append('<li onclick="$(this).remove();">' +
      '<input type="hidden" name="tags[]" value="' +
      $(select).val() + '" /> ' +
      $(select).find('option[selected]').text() + '</li>');
}



