# Defer a loaded rifle's opening reload on a line dodge · withheld

In fresh simulated 1068589, the bot began a voluntary 2.4s reload at 9/12 rounds during a real incoming line dodge and could not fire upon reacquiring the shooter. Validation compared exact local `ee3302588dcf34bd7990cdeb53a6754b0cc73210` to `b3d67472a42cae1fd989ca452c8296b2770d8ad1` in native and projectile-path evaluators. Deferring the reload advanced the first hit from about 15s to 13.3s and gained 90 damage dealt through three seconds at equal incoming. By six seconds it dealt 90 less in both models. Placements fell by one and two points respectively. The directed seed was found in a fresh 12-seed screen.

Validation voted to withhold. The candidate did not advance to survival or combat ballots or fresh rollout. A future change should confirm enough loaded rounds for the whole post-dodge exchange before disrupting the reload.
