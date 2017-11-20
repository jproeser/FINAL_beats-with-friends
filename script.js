SC.initialize({
  client_id: '6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn'
});

$(document).ready(function() {
  SC.get('/tracks', { genres: 'Hip Hop' }, function(tracks) {
    $(tracks).each(function(index, track) {
      $('#results').append($('<li></li>').html(track.title + ' - ' + track.genre));
    });
  });
});