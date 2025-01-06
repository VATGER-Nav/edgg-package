                          __          __ __    __            
    .--------.---.-.-----|  |--.--.--|__|  .--|  .-----.----.
    |        |  _  |  _  |  _  |  |  |  |  |  _  |  -__|   _|
    |__|__|__|___._|   __|_____|_____|__|__|_____|_____|__|  
                   |__|                                      
                                                             
**A generation utility for EuroScope Ground Radar and TopSky maps and settings using AIXM and KML.**

## GitHub Action

To run the mapbuilder GitHub action using a cache, see the following example:

```yaml
jobs:
  build-maps:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Restore cached sources
        uses: actions/cache/restore@v4
        with:
          path: .cache
          key: sources
      - name: Run mapbuilder
        uses: vatger-nav/mapbuilder@main
        with:
          # defaults
          target-path: '.'
          source-path: 'mapdata'
      - name: Store cached sources
        uses: actions/cache/save@v4
        with:
          path: .cache
          key: sources
```
