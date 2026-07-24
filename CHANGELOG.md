# Changelog

## [2.5.0](https://github.com/communitiesuk/hfu-share-webapp/compare/2.4.0...2.5.0) (2026-07-24)


### Features

* add new table to store hidden unassigned ARs (HFURB-3937) ([#43](https://github.com/communitiesuk/hfu-share-webapp/issues/43)) ([3234e09](https://github.com/communitiesuk/hfu-share-webapp/commit/3234e09456f04394ef67731a358a9312ca152037))


### Bug Fixes

* HFURB-2926 create a helper for shared render_postcode function ([#40](https://github.com/communitiesuk/hfu-share-webapp/issues/40)) ([9107bc0](https://github.com/communitiesuk/hfu-share-webapp/commit/9107bc068157f0bb5b02067d3db9009383620b53))

## [2.4.0](https://github.com/communitiesuk/hfu-share-webapp/compare/2.3.0...2.4.0) (2026-07-23)


### Features

* available links context processor and update nav ([#38](https://github.com/communitiesuk/hfu-share-webapp/issues/38)) ([9683aec](https://github.com/communitiesuk/hfu-share-webapp/commit/9683aeca787c50715bf8182a8aafec9b3c4cb146))
* mount deduplication app at /deduplication and consolidate its urls ([#39](https://github.com/communitiesuk/hfu-share-webapp/issues/39)) ([75bd059](https://github.com/communitiesuk/hfu-share-webapp/commit/75bd059b9b1f11d8cf45fbc5798faca32f2e4264))


### Bug Fixes

* HFURB-2797 horizontal margins across pages consistency ([#30](https://github.com/communitiesuk/hfu-share-webapp/issues/30)) ([d59623f](https://github.com/communitiesuk/hfu-share-webapp/commit/d59623f5f726ab542add8ed0d3bb5a07e11600d7))
* HFURB-2797++ move includes to the right position in two base templates ([#34](https://github.com/communitiesuk/hfu-share-webapp/issues/34)) ([dc074c2](https://github.com/communitiesuk/hfu-share-webapp/commit/dc074c21cc968954ecbdf3cc7c40e96466510bcf))
* HFURB-3322 make the page layouts use the grid classes rather than override ([#37](https://github.com/communitiesuk/hfu-share-webapp/issues/37)) ([f01479a](https://github.com/communitiesuk/hfu-share-webapp/commit/f01479a8a0fa078c5466eb6a3652d97bfba0578a))
* make some minor improvements to the service navigation ([#32](https://github.com/communitiesuk/hfu-share-webapp/issues/32)) ([8c3f3bb](https://github.com/communitiesuk/hfu-share-webapp/commit/8c3f3bb94d23ce019ed43ec69b6c8d1960023833))
* remove redundant margin classes from accessibility and cookies templates ([#41](https://github.com/communitiesuk/hfu-share-webapp/issues/41)) ([5da614c](https://github.com/communitiesuk/hfu-share-webapp/commit/5da614c96b391ff50f43804a3c27e34b8bb4d744))
* remove redundant margin-top classes from various templates ([#33](https://github.com/communitiesuk/hfu-share-webapp/issues/33)) ([35e2e14](https://github.com/communitiesuk/hfu-share-webapp/commit/35e2e14f60478fa3c311d9b16c529f83681057b9))
* update guest filter to handle trailing white space (HFURB-2458) ([#36](https://github.com/communitiesuk/hfu-share-webapp/issues/36)) ([2fefa48](https://github.com/communitiesuk/hfu-share-webapp/commit/2fefa4812fca129076d079be123d81d10adcc4d7))
* update style on some links ([#35](https://github.com/communitiesuk/hfu-share-webapp/issues/35)) ([2d1d125](https://github.com/communitiesuk/hfu-share-webapp/commit/2d1d1250e46359cd929f0ecff3f33f00b7ea976c))

## [2.3.0](https://github.com/communitiesuk/hfu-share-webapp/compare/2.2.0...2.3.0) (2026-07-21)


### Features

* add error handling for non-principal records in deduplication process ([#23](https://github.com/communitiesuk/hfu-share-webapp/issues/23)) ([3328f90](https://github.com/communitiesuk/hfu-share-webapp/commit/3328f900fd02c3dca6e01856ae6f906b706c4790))
* add new django admin action to update guest titles (HFURB-2458) ([#12](https://github.com/communitiesuk/hfu-share-webapp/issues/12)) ([645563c](https://github.com/communitiesuk/hfu-share-webapp/commit/645563c76dc158de6065ef14f79f30b13d10416b))
* HFURB-2611 Handle file attachments from GOV.UK Forms ([#18](https://github.com/communitiesuk/hfu-share-webapp/issues/18)) ([70e41ac](https://github.com/communitiesuk/hfu-share-webapp/commit/70e41aceabad3bb33679c5d586c50e2089f1cca0))
* HFURB-3081 update footer to use the correct GOV.UK Footer design ([#26](https://github.com/communitiesuk/hfu-share-webapp/issues/26)) ([0f72876](https://github.com/communitiesuk/hfu-share-webapp/commit/0f728766785c97750e4c4cc2c107456d87761c1f))
* HFURB-3377 allow appropriate admin users to access the actions tab for accommodation, guests and sponsors and to undo dedupe ([#15](https://github.com/communitiesuk/hfu-share-webapp/issues/15)) ([6284e78](https://github.com/communitiesuk/hfu-share-webapp/commit/6284e78a847df6b97e17952ca5e80a5541e96681))
* HFURB-3870 undo dedupe now archives records instead of deleting ([#16](https://github.com/communitiesuk/hfu-share-webapp/issues/16)) ([a7316ba](https://github.com/communitiesuk/hfu-share-webapp/commit/a7316ba5869a3d76b9704767b08e8f37c5ff56f8))
* HFURB-3871 hide archived records from views ([#17](https://github.com/communitiesuk/hfu-share-webapp/issues/17)) ([e3bd0e4](https://github.com/communitiesuk/hfu-share-webapp/commit/e3bd0e4451d320449e4015f7af7fb1c849d82d13))
* show archived records in admin ([#20](https://github.com/communitiesuk/hfu-share-webapp/issues/20)) ([98a5857](https://github.com/communitiesuk/hfu-share-webapp/commit/98a5857b64736b35718c0996b4d12b5a5f45a01f))
* update content for deduplication journey ([#22](https://github.com/communitiesuk/hfu-share-webapp/issues/22)) ([b0eb95d](https://github.com/communitiesuk/hfu-share-webapp/commit/b0eb95d3d1713b260b5f56b96fd2c7a7403a6626))
* update UAMs list view content (HFURB-3003) ([#28](https://github.com/communitiesuk/hfu-share-webapp/issues/28)) ([6f584f8](https://github.com/communitiesuk/hfu-share-webapp/commit/6f584f8cca30712ee8e21d5947bbf83c9b659555))


### Bug Fixes

* add ltla and ultla filters to the accomodation model ([5bbff85](https://github.com/communitiesuk/hfu-share-webapp/commit/5bbff8568d9668d33a3b43ef07212fba53f092c5))
* add test for the accomodations filters ([#11](https://github.com/communitiesuk/hfu-share-webapp/issues/11)) ([5bbff85](https://github.com/communitiesuk/hfu-share-webapp/commit/5bbff8568d9668d33a3b43ef07212fba53f092c5))
* HFURB-3313 add method to escape invalid starting characters in CSV ([#29](https://github.com/communitiesuk/hfu-share-webapp/issues/29)) ([f989650](https://github.com/communitiesuk/hfu-share-webapp/commit/f9896505bf7980c98219446b2f56d82c5f31a200))
* HFURB-3376 add undo dedupe message back ([#13](https://github.com/communitiesuk/hfu-share-webapp/issues/13)) ([535cbd6](https://github.com/communitiesuk/hfu-share-webapp/commit/535cbd6e218361d31de0df13421d74c464e62d6d))
* Include link to release notes in slack release notifications [HFURB-2233] ([#24](https://github.com/communitiesuk/hfu-share-webapp/issues/24)) ([8e871e3](https://github.com/communitiesuk/hfu-share-webapp/commit/8e871e3aef41b5485f0b36218206f3e497906f02))
* Replace trust authentication with password authentication [HFURB-3858] ([#27](https://github.com/communitiesuk/hfu-share-webapp/issues/27)) ([f59b873](https://github.com/communitiesuk/hfu-share-webapp/commit/f59b873c59484a67a9a676ea3ff3f28e380abe98))
* update the test files ([5bbff85](https://github.com/communitiesuk/hfu-share-webapp/commit/5bbff8568d9668d33a3b43ef07212fba53f092c5))

## [2.2.0](https://github.com/communitiesuk/hfu-share-webapp/compare/2.1.1...2.2.0) (2026-07-09)


### Features

* HFURB-3869 add archived fields to duplicate groups and related models ([#7](https://github.com/communitiesuk/hfu-share-webapp/issues/7)) ([078d882](https://github.com/communitiesuk/hfu-share-webapp/commit/078d882c75a78213601684f3ed0b22d30576a864))


### Bug Fixes

* dedupe readonly field html escaping ([#2](https://github.com/communitiesuk/hfu-share-webapp/issues/2)) ([3ebe0ac](https://github.com/communitiesuk/hfu-share-webapp/commit/3ebe0acf53c78a826b9a9c7ed366825df0b90654))
* fix lock file ([#5](https://github.com/communitiesuk/hfu-share-webapp/issues/5)) ([349a876](https://github.com/communitiesuk/hfu-share-webapp/commit/349a8764c32f0b9b46cfb58ad21860192e7e1efe))
* HFURB-2778 dropdown filter bug selecting arrow ([#10](https://github.com/communitiesuk/hfu-share-webapp/issues/10)) ([ef23b4f](https://github.com/communitiesuk/hfu-share-webapp/commit/ef23b4fa0d209ca5083ccd444d73ca81133a26e2))
* update unique application numbers in visa application flaky tests ([#9](https://github.com/communitiesuk/hfu-share-webapp/issues/9)) ([a8753e0](https://github.com/communitiesuk/hfu-share-webapp/commit/a8753e0c4e275a5ca797a0886331ca9fca5157d1))


### Documentation

* update links to local dev server in README ([#6](https://github.com/communitiesuk/hfu-share-webapp/issues/6)) ([888cd7b](https://github.com/communitiesuk/hfu-share-webapp/commit/888cd7b54bfa07e5e087491d70adf3a0fabb6dff))

## [2.1.1](https://github.com/communitiesuk/hfu-share-webapp/compare/2.1.1) (2026-07-07)

### Bug Fixes

For changelog entries prior to 2.0.2 see https://github.com/communitiesuk/hfu-case-management-webapp.
