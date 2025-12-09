
document.addEventListener("DOMContentLoaded", function() {
    // When user types a new goal - enable target amount
    document.getElementById("new_goal").addEventListener("input", function() {
        let targetInput = document.getElementById("target_amount");
        if (this.value.trim() !== "") {
            targetInput.disabled = false;
        }
        else {
            targetInput.disabled = true;
            targetInput.value = "";
        }
    });


    // When user picks an existing goal - disable target amount
    document.querySelector("select[name='goal_id']").addEventListener("change", function() {
        let targetInput = document.getElementById("target_amount");
        let newGoalInput = document.getElementById("new_goal")

        if (this.value !== "") {
            // existing goal selected
            targetInput.disabled = true;
            targetInput.value = "";
            newGoalInput.value = "";
        }
    });


});


