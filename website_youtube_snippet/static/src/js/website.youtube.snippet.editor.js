odoo.define('website_youtube_snippet.editor', function (require) {
'use strict';

var Model = require('web.Model');
var base = require('web_editor.base');
var options = require('web_editor.snippets.options');
var core = require('web.core');
var session = require('web.session');
var website = require('website.website');
var ajax = require('web.ajax');
var qweb = core.qweb;

ajax.loadXML('/website_youtube_snippet/static/src/xml/youtube_modal.xml', qweb);

// ------------------------ YOUTUBE CONFIG ----------------------
options.registry.youtube_embed = options.Class.extend({
    drop_and_build_snippet: function() {
        var self = this;

    	this.template = 'website_youtube_snippet.youtube_embed';
    	self.$modal = $( qweb.render(this.template, {}) );

        //Remove previous instance first
        $('#youtubeEmbedModal').remove();

    	$('body').append(self.$modal);

        $('#youtubeEmbedModal').modal('show');

        $('body').on('click', '#save_youtube_embed', function() {
		    var embed_code = self.$modal.find("#youtube_embed_code").val();

		    //Have to generate the iframe here since I can't have the iframe in the actual html
		    var snippet_output = "";
            snippet_output += "  <iframe class=\"embed-responsive-item\" t-attf-src=\"//www.youtube.com/embed/" + embed_code + "?theme=light\" allowFullScreen=\"true\" frameborder=\"0\"/>\n";

		    self.$target.html(snippet_output);
            $('#youtubeEmbedModal').modal('hide');
        });

    },
});


});