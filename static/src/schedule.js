let scheduleGrid;

let currentYear;
let currentWeek;

let currentYearText;
let currentWeekText;

let mondayDateText;
let tuesdayDateText;
let wednesdayDateText;
let thursdayDateText;
let fridayDateText;
let saturdayDateText;
let sundayDateText;

const MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec"
]

window.onload = () => {
    currentYear = new Date().getFullYear();
    currentWeek = getISOWeekNumber();

    currentYearText = document.getElementById("current-year");
    currentWeekText = document.getElementById("current-week");

    mondayDateText = document.getElementById("monday-date");
    tuesdayDateText = document.getElementById("tuesday-date");
    wednesdayDateText = document.getElementById("wednesday-date");
    thursdayDateText = document.getElementById("thursday-date");
    fridayDateText = document.getElementById("friday-date");
    saturdayDateText = document.getElementById("saturday-date");
    sundayDateText = document.getElementById("sunday-date");

    document.getElementById("this-week-button").onclick = () => {
        currentYear = new Date().getFullYear();
        currentWeek = getISOWeekNumber();

        update();
    };

    scheduleGrid = document.getElementById("schedule-grid");

    update();
}

function loadSchedule() {
    Array.from(document.getElementsByClassName("user-row")).forEach(e => e.remove());
    fetch(window.location.origin = `/schedule?year=${currentYear}&week=${currentWeek}&pp=true`)
        .then(response => {
            if (response.status !== 200) {
                return;
            }

            response.json().then(data => {
                console.log(data);

                Object.keys(data).sort((a, b) => data[a][0] - data[b][0]).forEach(k => {
                    scheduleGrid.appendChild(userRow(k, data[k].slice(1)));
                });
            });
        });
}

function userRow(name, times) {
    let el = document.createElement("div");
    el.classList.add("user-row");
    el.innerHTML += `<p>${name}</p>`;

    times.forEach(t => {
        if (t === null) {
            el.innerHTML += "<p></p>";
        } else if (t.toLowerCase().endsWith("afw")) {
            el.innerHTML += `<p>${t.slice(0, 5)}  <i class="fa-solid fa-sink"></i></p>`;
        } else {
            el.innerHTML += `<p>${t}</p>`;
        }
    });

    return el;
}

function update() {
    currentYearText.innerText = currentYear;
    currentWeekText.innerText = `Week ${currentWeek}`;

    document.title = `${currentYear} - Week ${currentWeek}`;

    let start = moment(`${currentYear}W${currentWeek.toString().padStart(2, '0')}`).toDate();

    let dates = [mondayDateText, tuesdayDateText, wednesdayDateText, thursdayDateText, fridayDateText, saturdayDateText, sundayDateText];

    for (let i = 0; i < 7; i++) {
        let d = new Date(start);
        d.setDate(d.getDate() + i);

        dates[i].innerText = `${d.getDate()} ${MONTHS[d.getMonth()]}`;
    }

    loadSchedule();
}

function increaseYear() {
    currentYear++;

    update();
}

function decreaseYear() {
    if (currentYear > 0) {
        currentYear--;
    }

    update();
}

function increaseWeek() {
    if (currentWeek === 52) {
        currentYear++;
        currentWeek = 1;
    } else {
        currentWeek++;
    }

    update();
}

function decreaseWeek() {
    if (currentWeek === 1) {
        currentYear--;
        currentWeek = 52;
    } else {
        currentWeek--;
    }

    update();
}

function getISOWeekNumber(date) {
    const currentDate = date || new Date();
    currentDate.setHours(0, 0, 0, 0);
    currentDate.setDate(currentDate.getDate() + 4 - (currentDate.getDay() || 7));
    const startOfYear = new Date(currentDate.getFullYear(), 0, 1);
    return Math.ceil(((currentDate - startOfYear) / 86400000 + 1) / 7);
}