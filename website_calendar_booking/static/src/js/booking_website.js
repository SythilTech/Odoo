odoo.define('booking.website', function (require) {
'use strict';

var ajax = require('web.ajax');
var core = require('web.core');
var qweb = core.qweb;

ajax.loadXML('/website_calendar_booking/static/src/xml/website_calendar_booking_modal1.xml', qweb);

$(document).ready(function() {

        // page is now ready, initialize the calendar...
        var slotDuration = convert_float_time( $("#calendar_slot_duration").val() );
        var minTime = $("#calendar_min_time").val();
        var maxTime = $("#calendar_max_time").val();
        var user = $("#calendar_user").val();
        var calendarID = $("#calendar_id").val();

        $('#booking_calendar').fullCalendar({
            // put your options and callbacks here
            minTime: minTime,
            maxTime: maxTime,
            slotDuration: slotDuration + ':00',
            slotLabelInterval: '00:' + slotDuration + ':00',
            slotLabelFormat: 'hh:mma',
            defaultView: 'agendaWeek',
            timezone: 'local',
            allDaySlot: false,
            eventSources: [
                {
                url: '/book/calendar/timeframe/' + calendarID,
                rendering: 'background',
                className: "booking_calendar_book_time"
                },
                {
                url: '/book/calendar/events/' + user,
                rendering: 'background',
                backgroundColor: '#ff0000'
                }
            ],
           dayClick: function(date, jsEvent, view) {


               var allEvents = [];
               allEvents = $('#booking_calendar').fullCalendar('clientEvents');
               var event = $.grep(allEvents, function (v) {
                   return +v.start === +date;
               });
               if (event.length == 0) {

                   this.template = 'website_calendar_booking.calendar_booking_modal';
    		       var self = this;
    		       self.$modal = $( qweb.render(this.template, {}) );
    		       $('body').append(self.$modal);
                   $('#oe_website_calendar_modal').modal('show');
                   $('#booking_form_start').val(date);
                   $('#booking_form_calendar_id').val(calendarID);

                   self.$modal.find("#submit_calendar_booking").on('click', function () {
                       self.$modal.modal('hide');
                   });

		   } else {
			   alert("This timeslot has already been booked");
		   }

           }
    }); //end fullcalendar load


function convert_float_time(float_time) {
    var format_time = ""
    var decimal = float_time % 1
    format_time = Math.floor(float_time) + ":" + (60 * decimal)
    return format_time
}

}); //End document load


});