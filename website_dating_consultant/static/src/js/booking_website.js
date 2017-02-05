odoo.define('booking.website', function (require) {
'use strict';

var ajax = require('web.ajax');
var core = require('web.core');
var qweb = core.qweb;

ajax.loadXML('/website_dating_consultant/static/src/xml/website_calendar_booking_modal1.xml', qweb);

$(document).ready(function() {

        // page is now ready, initialize the calendar...
        var slotDuration = $("#calendar_slot_duration").val();
        var consultantID = $("#consultant_id").val();

        $('#booking_calendar').fullCalendar({
            // put your options and callbacks here
            minTime: '05:00:00',
            maxTime: '22:00:00',
            slotDuration: '00:' + slotDuration + ':00',
            slotLabelInterval: '00:' + slotDuration + ':00',
            slotLabelFormat: 'hh:mma',
            defaultView: 'agendaWeek',
            timezone: 'local',
            allDaySlot: false,
            eventSources: [
                {
                url: '/dating/booking/timeframe/' + consultantID,
                rendering: 'background'
                //backgroundColor: '#00FF00'
                //className: "booking_calendar_book_time"
                },
                {
                url: '/dating/booking/events/' + consultantID,
                rendering: 'background',
                backgroundColor: '#FF0000'
                }

            ],
            eventClick: function(event) {
			    alert("Event Click");
            },
            dayClick: function(date, jsEvent, view) {


               var allEvents = [];
               allEvents = $('#booking_calendar').fullCalendar('clientEvents');
               var event = $.grep(allEvents, function (v) {
                   return +v.start === +date;
               });
               if (event.length == 0) {

                   this.template = 'website_dating_consultant.calendar_booking_modal';
    		       var self = this;
    		       self.$modal = $( qweb.render(this.template, {}) );
    		       $('body').append(self.$modal);
                   $('#oe_website_calendar_modal').modal('show');
                   $('#booking_form_start').val(date);
                   $('#booking_form_consultant_id').val(consultantID);

                   self.$modal.find("#submit_calendar_booking").on('click', function () {
                       self.$modal.modal('hide');
                   });

		       } else {
			       alert("This timeslot has already been booked");
		       }

           }
    }); //end fullcalendar load


}); //End document load


});