# Try gun clearance with magazine-aware targeting and sidesteps

Survival and combat voted **reject** and validation voted **revise** on `3ac6599196dcc84bd97595c6a73824788a54c1c2`. Its direct Git parent is `489c7211da0f707e27bba0741abf487fe084871e`. It applies the exact gun clearance patch and its own unit test from `88460d6e38f65a9cefaf9b24579fab25bb7f4a38`, preserving the magazine targeting and sidestep logic. The underlying target choice can change which rounds the clearance filter sees.

The owner 24 campus pairs gained 0.708 points per match (four improved, 17 tied, three worse). The separate 16 campus pairs lost 0.563 (two improved, ten tied, four worse). All 48 four-mech placement pairs tied. Independently replayed seed 953811 confirmed a one-round hold followed by an extra 45 damage to a different target. Later movement diverged and the candidate lost nine placement points. The immediate round economy was useful in that replay, while the full policy did not generalize across panels.

The exact code passed 24 unit tests and all 300 official replay observations. Keep the approved gun clearance on squad focus and the approved magazine-plus-sidestep candidate available separately.
