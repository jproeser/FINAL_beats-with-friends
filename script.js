SC.initialize({
  client_id: '6d3KZ6G4o4U0GLCiznHCjbQrT2Ee90cn',
  // redirect_uri: 'http://external.codecademy.com/soundcloud.html'
});

//////////////////////////////////AUTHENTICATION
$(document).ready(function() {
  $('a.connect').click(function(e) {
    e.preventDefault();
    SC.connect(function(){
        SC.get('/me', function(me){
            $('#username').html(me.username);
        });
    });
  });
});


//////////////////////////////////MAKING REQUESTS
// $(document).ready(function() {
//   SC.get('/tracks', { genres: 'Hip Hop' }, function(tracks) {
//     $(tracks).each(function(index, track) {
//       $('#results').append($('<li></li>').html(track.title + ' - ' + track.genre));
//     });
//   });
// });


// //////////////////////////////////FETCHING A SOUND TO PLAY
// $(document).ready(function() {
// SC.get('/tracks/293', function(track) {
//   SC.oEmbed(track.permalink_url, document.getElementById('player'));
// });

////////////////////////////////////EXPLORING SOUNDMANAGER OBJECTS - Make consistent sound players
// $(document).ready(function() {
//   SC.stream('/tracks/293', function(sound) {
//   });});

////////////////////////////////////PLAYING SOUNDS
// $(document).ready(function() {
// SC.stream('/tracks/293', function(sound) {
//   $('#start').click(function(e) {
//     e.preventDefault();
//     sound.start();
//   });
//   $('#stop').click(function(e) {
//     e.preventDefault();
//     sound.stop();
//   });
// });
// });



////////////////////////////////////ACCESSING COMMENTS ON A TRACK
// $(document).ready(function() {
//   SC.get('/tracks/293/comments', function(comments) {
//     $.each(comments, function(i, comment) {
//       $('#comments').append(
//         $('<li></li>').html(comment.body)
//       );
//     });
//   });
// });





////////////////////////////////////Triggering events with comments
// $(document).ready(function() {
//   SC.stream('/tracks/293', {
//      autoPlay: true,
//      ontimedcomments: function(comment) {comment[0].body} 
//   });
// });


////////////////////////////////////POSTING COMMENTS
// $(document).ready(function() {
//     SC.stream('/tracks/70355723', {
//         autoPlay: true
//     }, function(sound) {
//         window.sound = sound;
//     });
    
//     $('#comment_form').submit(function(e) {
//             e.preventDefault();
//             SC.connect(function() {
//                 SC.post('/tracks/70355723/comments', {
//                     comment: {
//                         body: $('#comment_body').val(),
//                         timestamp: window.sound.position
//                     }
//                 }, function(comment) {
//                     $('#status').val('Your comment was posted!');
//                     $('#comment_body').val('');
//                 });
//             });
//         });
// });



