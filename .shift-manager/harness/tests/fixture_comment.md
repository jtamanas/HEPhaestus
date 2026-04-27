# Test fixture: hidden banner token (in HTML comment)

This fixture contains the banner token ONLY inside an HTML comment.
It should NOT be found by the rendered-grep harness.

<!-- banner-token-xyz: This token is hidden in an HTML comment and must not be visible. -->

Some text after the comment with no token.
