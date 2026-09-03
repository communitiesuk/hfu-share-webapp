# Browser test seed scenarios

Catalog of every record scenario created by `python manage.py seed_browser_test_la`. The seeder wipes and recreates all data in the browser test local authority (LA) "Hobbiton (Browser test LTLA)", so this state is the baseline at the start of every browser test run.

Source of truth: `hfurb_scripts/seeders/stages/seed_browser_test_la.py` (`AR_SCENARIOS` table and the special scenario builders). If this file and the code disagree, the code wins; regenerate the details by running the command, which prints an example record id per scenario. Titles below come from a run with the default seed and are stable while the seed and seeder version stay unchanged.

## Fixed values

| Constant | Value |
| --- | --- |
| Test LA | Hobbiton (Browser test LTLA) |
| Test LA group | `ltla_hobbiton_browser_test` |
| Second LA (multi-LA and reassignment scenarios) | Isles of Scilly |
| Record id prefix | `browser-test` |
| Random seed | `BROWSER_TEST_SEED` env var, default 1313 |

Record ids are deterministic: counters reset each run, so ids follow creation order, for example `browser-test-ar-00001`, `browser-test-person-00003`, `browser-test-check-00002`. Guests, sponsors, accommodations, groups, visa applications and export tool objects hang off each accommodation request with the same prefix scheme (`person`, `sponsor`, `accommodation`, `group`, `visa`, `export`).

## Accommodation request scenarios

One accommodation request (AR) per row, created in this order. Guest count equals the number of visa statuses. Every checks status and AR status value appears at least once.

| # | AR id | Title | Checks status | Guest visa statuses | Extras |
| --- | --- | --- | --- | --- | --- |
| 1 | browser-test-ar-00001 | Jade Smith to Flat 95 | Checks required | Arrived | 2 case comments |
| 2 | browser-test-ar-00002 | Valerie Poole and 1 other to 25 Barlow tunn, BH60 2AD | Checks required | Arrived, Issued | |
| 3 | browser-test-ar-00003 | Jeremy Hunt and 2 others to Flat 65 | Checks partially completed | Confirmed, Arrived, Pending | 1 passed check |
| 4 | browser-test-ar-00004 | Debra Bell to 1 Julian forge, L9T 1HG | Checks completed | Arrived | 4 passed checks, 2 case comments |
| 5 | browser-test-ar-00005 | Kirsty Hawkins and 1 other to Studio 83 | Checks required | Issued, Refused | |
| 6 | browser-test-ar-00006 | Edward Schofield and 2 others to 582 Gerald thr, W02 6TR | Checks required | Arrived, Confirmed, Withdrawn | |
| 7 | browser-test-ar-00007 | Dominic Curtis to Flat 82T | Some checks failed | Arrived | 1 failed check, escalated when the failed check is an accommodation or sponsor check |
| 8 | browser-test-ar-00008 | Dylan Kaur and 1 other to Flat 11s | Checks completed | Pending, Lapsed | 4 passed checks |
| 9 | browser-test-ar-00009 | Tom Byrne and 2 others to Studio 3 | Checks required | Arrived, Arrived, Arrived | |
| 10 | browser-test-ar-00010 | Susan Robson to Flat 60 | Closed, left programme | Issued | leaving programme interaction ("Return to Ukraine") |
| 11 | browser-test-ar-00011 | Jonathan Greenwood and 1 other to 35 Amelia fiel, L8 1TQ | Checks partially completed | Confirmed, Arrived | 1 passed check, 2 case comments |
| 12 | browser-test-ar-00012 | Yvonne Smith and 2 others to Flat 95 | Checks completed | Pending, Arrived, Issued | 4 passed checks |
| 13 | browser-test-ar-00013 | Amber Ellis to Flat 4 | Checks required | Refused | unaccompanied minor (UAM, Flow Visa Pending) |
| 14 | browser-test-ar-00014 | Ian Yates and 1 other to Flat 32J | Checks required | Arrived, Confirmed | |
| 15 | browser-test-ar-00015 | Molly Mills and 2 others to 1 Melanie isle, CV1B 5WN | Checks partially completed | Withdrawn, Arrived, Pending | 1 passed check |
| 16 | browser-test-ar-00016 | Valerie Jordan to 756 Knight bri, N7 0JG | Checks completed | Lapsed | 4 passed checks, pending outbound reassignment to Isles of Scilly |
| 17 | browser-test-ar-00017 | Martyn Field and 1 other to 79 Owen stream, N4J 5SJ | Checks required | Arrived, Arrived | |
| 18 | browser-test-ar-00018 | Karen Brown and 2 others to 44 Clayton pra, L8S 3XY | Checks required | Arrived, Issued, Confirmed | |
| 19 | browser-test-ar-00019 | Diane Williams to 10 Helen pass,, KT5R 6RG | Closed, duplicate | Arrived | |
| 20 | browser-test-ar-00020 | Charlene Hussain and 1 other to Flat 76 | Checks completed | Pending, Arrived | 4 passed checks |
| 21 | browser-test-ar-00021 | Naomi Gibbs and 2 others to Flat 2 | Checks required | Issued, Refused, Arrived | receives the guest moved off the closed empty AR (#22) |
| 22 | browser-test-ar-00022 | Bernard Walton to Flat 98y | Closed, empty | Confirmed | its guest is moved to AR #21, leaving it with no people |
| 23 | browser-test-ar-00023 | Yvonne Palmer and 1 other to Studio 2 | Checks partially completed | Withdrawn, Arrived | 1 passed check |
| 24 | browser-test-ar-00024 | Leonard Arnold and 2 others to Flat 86 | Checks completed | Pending, Lapsed, Arrived | 4 passed checks |
| 25 | browser-test-ar-00025 | Antony Davies to Flat 77u | Cancelled | Arrived | |
| 26 | browser-test-ar-00026 | Howard Parker and 1 other to Flat 01d | Checks required | Arrived, Issued | |
| 27 | browser-test-ar-00027 | Rebecca Morgan and 2 others to Flat 69K | Checks partially completed | Confirmed, Arrived, Pending | 1 passed check |
| 28 | browser-test-ar-00028 | Diane Lowe to 53 Walsh divide, Hobbiton | In temporary accommodation | Arrived | accommodation type is temporary accommodation |
| 29 | browser-test-ar-00029 | Joan Daly and 1 other to 1 Warren dam, , BR94 2RZ | Checks required | Issued, Refused | |
| 30 | browser-test-ar-00030 | Helen Walker and 2 others to 6 Luke avenue,, L1 6XL | Checks required | Arrived, Confirmed, Withdrawn | |
| 31 | browser-test-ar-00031 | Peter Lowe to 78 Charlene cove, Hobbiton | Pre-arrival checks complete | Arrived | |
| 32 | browser-test-ar-00032 | Albert Gibson and 1 other to Flat 7 | Checks completed | Pending, Lapsed | 4 passed checks |
| 33 | browser-test-ar-00033 | Harriet Thompson and 2 others to Flat 1 | Checks required | Arrived, Arrived, Arrived | |
| 34 | browser-test-ar-00034 | Charlene Davies to Flat 98 | Checks required | Issued | AR status: Missing accommodation |
| 35 | browser-test-ar-00035 | Joseph Thompson and 1 other to 189 Davison sp, SK9 6ZB | Checks partially completed | Confirmed, Arrived | 1 passed check |
| 36 | browser-test-ar-00036 | Clive Evans and 2 others to Flat 1 | Checks completed | Pending, Arrived, Issued | 4 passed checks |
| 37 | browser-test-ar-00037 | Stacey Harvey to 24 Ferguson pines, Hobbiton | Checks required | Refused | AR status: Arrival confirmed, unaccompanied minor (UAM, Flow Visa Pending) |
| 38 | browser-test-ar-00038 | Gerard Simpson and 1 other to 57 Gibson pine, SP21 6AP | Checks required | Arrived, Confirmed | multi-LA sponsor: the sponsor also owns a property in Isles of Scilly |
| 39 | browser-test-ar-00039 | Howard Johnson and 2 others to 8 Fowler trail, PO4X 3EQ | Checks partially completed | Withdrawn, Arrived, Pending | 1 passed check, rejected outbound reassignment to Isles of Scilly |
| 40 | browser-test-ar-00040 | Shane Adams to 2 Hardy valley, HG31 6BP | Checks completed | Lapsed | 4 passed checks, multi-LA AR: extended with a second accommodation, sponsor and unique application number in Isles of Scilly, plus a Pending visa application per guest, so it spans two LAs |

## Special scenarios created after the table

| Scenario | AR id | Title | Detail |
| --- | --- | --- | --- |
| Inbound accepted reassignment | browser-test-ar-00041 | Thomas Simpson | Built in Isles of Scilly with checks status Rematch required, then reassigned into the test LA with an accepted reassignment request ("Sponsorship placement broke down"), a rematch interaction, accommodation removed and hosts unlinked (which is why the title has no address) |
| Deduplicated guest pair | browser-test-ar-00042 | Eileen Austin to 76 Helen sprin, B8 3RS | One guest plus a near-duplicate (same name, date of birth and passport, surname uppercased), merged through a GuestDuplicateGroup by the browser test user |
| Deduplicated sponsor pair | browser-test-ar-00043 | Abigail Richards to 8 Callum branc, N6W 4NY | One sponsor plus a near-duplicate (same email and date of birth, surname lowercased), merged through a SponsorDuplicateGroup by the browser test user |

## Visa information requests

Three conversations attached to the first three visa applications in the test LA (ordered by visa application id):

| Label | Status | Conversation |
| --- | --- | --- |
| VIR awaiting LA | Awaiting LA | 1 UKVI message asking whether the guest still resides at the sponsor's address |
| VIR awaiting UKVI | Awaiting UKVI | UKVI asks for the arrival date, the LA replies confirming it |
| VIR closed | Closed | UKVI asks whether guests are known, the LA confirms, UKVI closes the request |

UK Visas and Immigration (UKVI) messages are authored as `browser-test-ukvi`; LA replies are authored as the browser test user.

## Checks statuses and what they seed

| Checks status | Seeded checks |
| --- | --- |
| Checks required | none |
| Checks partially completed | 1 passed check (random type from: accommodation suitable, accommodation exists, sponsor DBS, group arrived) |
| Checks completed | all 4 check types passed |
| Some checks failed | 1 failed check with a failure reason; when it is an accommodation or sponsor check, an escalated safeguarding check is raised through the real form |
| Closed, left programme | a "Return to Ukraine" leaving programme interaction |

## Case comments

Accommodation requests flagged with case comments (#1, #4, #11) each get 2 comments, drawn in order from a fixed list of 6 comment texts with fixed dates between June and September 2025, authored by the browser test user.


## All seeded records

Every record the seeder creates, grouped by model, in creation order. Generated from a seeded local database with the default seed.

### Guests (MvPerson)

| Id | Name | Visa status | AR |
| --- | --- | --- | --- |
| browser-test-person-00001 | Jade Smith | Arrived | browser-test-ar-00001 |
| browser-test-person-00002 | Valerie Poole | Arrived | browser-test-ar-00002 |
| browser-test-person-00003 | Philip Berry | Issued | browser-test-ar-00002 |
| browser-test-person-00004 | Dominic Hill | Confirmed | browser-test-ar-00003 |
| browser-test-person-00005 | Abbie Barnett | Arrived | browser-test-ar-00003 |
| browser-test-person-00006 | Jeremy Hunt | Pending | browser-test-ar-00003 |
| browser-test-person-00007 | Debra Bell | Arrived | browser-test-ar-00004 |
| browser-test-person-00008 | Reece Rice | Issued | browser-test-ar-00005 |
| browser-test-person-00009 | Kirsty Hawkins | Refused | browser-test-ar-00005 |
| browser-test-person-00010 | Barbara Reid | Arrived | browser-test-ar-00006 |
| browser-test-person-00011 | Edward Schofield | Confirmed | browser-test-ar-00006 |
| browser-test-person-00012 | Kerry Lowe | Withdrawn | browser-test-ar-00006 |
| browser-test-person-00013 | Dominic Curtis | Flow Visa Pending | browser-test-ar-00007 |
| browser-test-person-00014 | Julie Cole | Pending | browser-test-ar-00008 |
| browser-test-person-00015 | Dylan Kaur | Lapsed | browser-test-ar-00008 |
| browser-test-person-00016 | Jake Edwards | Arrived | browser-test-ar-00009 |
| browser-test-person-00017 | Tom Byrne | Arrived | browser-test-ar-00009 |
| browser-test-person-00018 | Aimee Thomas | Arrived | browser-test-ar-00009 |
| browser-test-person-00019 | Susan Robson | Issued | browser-test-ar-00010 |
| browser-test-person-00020 | Lesley Williams | Confirmed | browser-test-ar-00011 |
| browser-test-person-00021 | Jonathan Greenwood | Arrived | browser-test-ar-00011 |
| browser-test-person-00022 | Yvonne Smith | Pending | browser-test-ar-00012 |
| browser-test-person-00023 | Alexander Martin | Arrived | browser-test-ar-00012 |
| browser-test-person-00024 | Kayleigh Reynolds | Issued | browser-test-ar-00012 |
| browser-test-person-00025 | Amber Ellis | Flow Visa Pending | browser-test-ar-00013 |
| browser-test-person-00026 | Megan Rowley | Arrived | browser-test-ar-00014 |
| browser-test-person-00027 | Ian Yates | Confirmed | browser-test-ar-00014 |
| browser-test-person-00028 | Neil Connolly | Withdrawn | browser-test-ar-00015 |
| browser-test-person-00029 | Angela Patterson | Arrived | browser-test-ar-00015 |
| browser-test-person-00030 | Molly Mills | Pending | browser-test-ar-00015 |
| browser-test-person-00031 | Valerie Jordan | Lapsed | browser-test-ar-00016 |
| browser-test-person-00032 | Martyn Field | Arrived | browser-test-ar-00017 |
| browser-test-person-00033 | Kim Cooper | Arrived | browser-test-ar-00017 |
| browser-test-person-00034 | Karen Brown | Arrived | browser-test-ar-00018 |
| browser-test-person-00035 | Barry Harris | Issued | browser-test-ar-00018 |
| browser-test-person-00036 | Barbara Smith | Confirmed | browser-test-ar-00018 |
| browser-test-person-00037 | Diane Williams | Arrived | browser-test-ar-00019 |
| browser-test-person-00038 | Rosemary Thomas | Pending | browser-test-ar-00020 |
| browser-test-person-00039 | Charlene Hussain | Arrived | browser-test-ar-00020 |
| browser-test-person-00040 | Ashleigh Kelly | Issued | browser-test-ar-00021 |
| browser-test-person-00041 | Rhys Wood | Refused | browser-test-ar-00021 |
| browser-test-person-00042 | Naomi Gibbs | Arrived | browser-test-ar-00021 |
| browser-test-person-00043 | Bernard Walton | Confirmed | browser-test-ar-00021 |
| browser-test-person-00044 | Yvonne Palmer | Withdrawn | browser-test-ar-00023 |
| browser-test-person-00045 | Bernard Kerr | Arrived | browser-test-ar-00023 |
| browser-test-person-00046 | Donald Butler | Pending | browser-test-ar-00024 |
| browser-test-person-00047 | Georgia McDonald | Lapsed | browser-test-ar-00024 |
| browser-test-person-00048 | Leonard Arnold | Arrived | browser-test-ar-00024 |
| browser-test-person-00049 | Antony Davies | Arrived | browser-test-ar-00025 |
| browser-test-person-00050 | Howard Parker | Arrived | browser-test-ar-00026 |
| browser-test-person-00051 | Tina Farmer | Issued | browser-test-ar-00026 |
| browser-test-person-00052 | Rebecca Morgan | Confirmed | browser-test-ar-00027 |
| browser-test-person-00053 | Francesca Young | Arrived | browser-test-ar-00027 |
| browser-test-person-00054 | Andrea West | Pending | browser-test-ar-00027 |
| browser-test-person-00055 | Diane Lowe | Flow Visa Pending | browser-test-ar-00028 |
| browser-test-person-00056 | Joan Daly | Issued | browser-test-ar-00029 |
| browser-test-person-00057 | Glen Davies | Refused | browser-test-ar-00029 |
| browser-test-person-00058 | Paul Parker | Arrived | browser-test-ar-00030 |
| browser-test-person-00059 | Helen Walker | Confirmed | browser-test-ar-00030 |
| browser-test-person-00060 | Fiona Taylor | Withdrawn | browser-test-ar-00030 |
| browser-test-person-00061 | Peter Lowe | Flow Visa Pending | browser-test-ar-00031 |
| browser-test-person-00062 | Albert Gibson | Pending | browser-test-ar-00032 |
| browser-test-person-00063 | Wayne Turner | Lapsed | browser-test-ar-00032 |
| browser-test-person-00064 | Harriet Thompson | Arrived | browser-test-ar-00033 |
| browser-test-person-00065 | Samuel Bates | Arrived | browser-test-ar-00033 |
| browser-test-person-00066 | Sally Watson | Arrived | browser-test-ar-00033 |
| browser-test-person-00067 | Charlene Davies | Issued | browser-test-ar-00034 |
| browser-test-person-00068 | Teresa Smith | Confirmed | browser-test-ar-00035 |
| browser-test-person-00069 | Joseph Thompson | Arrived | browser-test-ar-00035 |
| browser-test-person-00070 | Gregory Mitchell | Pending | browser-test-ar-00036 |
| browser-test-person-00071 | Clive Evans | Arrived | browser-test-ar-00036 |
| browser-test-person-00072 | Sheila Davis | Issued | browser-test-ar-00036 |
| browser-test-person-00073 | Stacey Harvey | Flow Visa Pending | browser-test-ar-00037 |
| browser-test-person-00074 | Charlie Lewis | Arrived | browser-test-ar-00038 |
| browser-test-person-00075 | Gerard Simpson | Confirmed | browser-test-ar-00038 |
| browser-test-person-00076 | Howard Johnson | Withdrawn | browser-test-ar-00039 |
| browser-test-person-00077 | Sarah Barrett | Arrived | browser-test-ar-00039 |
| browser-test-person-00078 | Julia Evans | Pending | browser-test-ar-00039 |
| browser-test-person-00079 | Shane Adams | Lapsed | browser-test-ar-00040 |
| browser-test-person-00080 | Thomas Simpson | Confirmed | browser-test-ar-00041 |
| browser-test-person-00081 | Eileen Austin | Confirmed | browser-test-ar-00042 |
| browser-test-person-00082 | Eileen AUSTIN | Confirmed |  |
| browser-test-person-00083 | Abigail Richards | Confirmed | browser-test-ar-00043 |

### Sponsors (MvVolunteer)

| Id | Name | AR(s) |
| --- | --- | --- |
| browser-test-sponsor-00001 | Josephine Smith | browser-test-ar-00001 |
| browser-test-sponsor-00002 | Lorraine Thomas | browser-test-ar-00002 |
| browser-test-sponsor-00003 | Christopher Bryan | browser-test-ar-00003 |
| browser-test-sponsor-00004 | Ashley Thomas | browser-test-ar-00004 |
| browser-test-sponsor-00005 | Michael Murphy | browser-test-ar-00005 |
| browser-test-sponsor-00006 | Alexander Wright | browser-test-ar-00006 |
| browser-test-sponsor-00007 | Jemma Davies | browser-test-ar-00007 |
| browser-test-sponsor-00008 | Gillian Hussain | browser-test-ar-00008 |
| browser-test-sponsor-00009 | Adrian Davey | browser-test-ar-00009 |
| browser-test-sponsor-00010 | Lindsey Smith | browser-test-ar-00010 |
| browser-test-sponsor-00011 | Adrian Gardner | browser-test-ar-00011 |
| browser-test-sponsor-00012 | Luke Little | browser-test-ar-00012 |
| browser-test-sponsor-00013 | Kayleigh Jones | browser-test-ar-00013 |
| browser-test-sponsor-00014 | Scott Fletcher | browser-test-ar-00014 |
| browser-test-sponsor-00015 | Ben Bull | browser-test-ar-00015 |
| browser-test-sponsor-00016 | Raymond Kelly | browser-test-ar-00016 |
| browser-test-sponsor-00017 | Hayley Hardy | browser-test-ar-00017 |
| browser-test-sponsor-00018 | Heather Williams | browser-test-ar-00018 |
| browser-test-sponsor-00019 | Jason Kerr | browser-test-ar-00019 |
| browser-test-sponsor-00020 | Gerald Wilson | browser-test-ar-00020 |
| browser-test-sponsor-00021 | Sophie Hill | browser-test-ar-00021 |
| browser-test-sponsor-00022 | Geoffrey Burton | browser-test-ar-00022 |
| browser-test-sponsor-00023 | Nicholas Kirby | browser-test-ar-00023 |
| browser-test-sponsor-00024 | Pauline Walker | browser-test-ar-00024 |
| browser-test-sponsor-00025 | Damien Robson | browser-test-ar-00025 |
| browser-test-sponsor-00026 | Jacqueline Cook | browser-test-ar-00026 |
| browser-test-sponsor-00027 | Catherine Pugh | browser-test-ar-00027 |
| browser-test-sponsor-00028 | Deborah Rogers | browser-test-ar-00028 |
| browser-test-sponsor-00029 | Justin Kennedy | browser-test-ar-00029 |
| browser-test-sponsor-00030 | Colin Khan | browser-test-ar-00030 |
| browser-test-sponsor-00031 | Amanda Jackson | browser-test-ar-00031 |
| browser-test-sponsor-00032 | Nicholas Thompson | browser-test-ar-00032 |
| browser-test-sponsor-00033 | Gemma Patterson | browser-test-ar-00033 |
| browser-test-sponsor-00034 | Georgina Smith | browser-test-ar-00034 |
| browser-test-sponsor-00035 | Anna Khan | browser-test-ar-00035 |
| browser-test-sponsor-00036 | Jack Wheeler | browser-test-ar-00036 |
| browser-test-sponsor-00037 | Leonard Skinner | browser-test-ar-00037 |
| browser-test-sponsor-00038 | Sam Ward | browser-test-ar-00038 |
| browser-test-sponsor-00039 | Julian Baker | browser-test-ar-00039 |
| browser-test-sponsor-00040 | Joe Wilson | browser-test-ar-00040 |
| browser-test-sponsor-00041 | Natasha Murray | browser-test-ar-00040 |
| browser-test-sponsor-00042 | Julie Smith | browser-test-ar-00041 |
| browser-test-sponsor-00043 | June Evans | browser-test-ar-00042 |
| browser-test-sponsor-00044 | Heather Hudson |  |
| browser-test-sponsor-00045 | Heather hudson |  |

### Accommodations (MvAccommodation)

| Id | Address | LA | AR(s) |
| --- | --- | --- | --- |
| browser-test-accommodation-00001 | Flat 95
Lee path, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00001 |
| browser-test-accommodation-00002 | 25 Barlow tunnel, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00002 |
| browser-test-accommodation-00003 | Flat 65
Hazel crossing, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00003 |
| browser-test-accommodation-00004 | 1 Julian forge, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00004 |
| browser-test-accommodation-00005 | Studio 83
Evans canyon, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00005 |
| browser-test-accommodation-00006 | 582 Gerald throughway, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00006 |
| browser-test-accommodation-00007 | Flat 82T
Patrick wall, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00007 |
| browser-test-accommodation-00008 | Flat 11s
Williams meadow, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00008 |
| browser-test-accommodation-00009 | Studio 3
Anthony plaza, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00009 |
| browser-test-accommodation-00010 | Flat 60
Gary oval, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00010 |
| browser-test-accommodation-00011 | 35 Amelia field, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00011 |
| browser-test-accommodation-00012 | Flat 95
Roy crest, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00012 |
| browser-test-accommodation-00013 | Flat 4
Irene river, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00013 |
| browser-test-accommodation-00014 | Flat 32J
Bates lodge, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00014 |
| browser-test-accommodation-00015 | 1 Melanie isle, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00015 |
| browser-test-accommodation-00016 | 756 Knight bridge, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00016 |
| browser-test-accommodation-00017 | 79 Owen stream, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00017 |
| browser-test-accommodation-00018 | 44 Clayton prairie, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00018 |
| browser-test-accommodation-00019 | 10 Helen pass, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00019 |
| browser-test-accommodation-00020 | Flat 76
Jeffrey run, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00020 |
| browser-test-accommodation-00021 | Flat 2
Swift meadows, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00021 |
| browser-test-accommodation-00022 | Flat 98y
Rosie ridges, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00022 |
| browser-test-accommodation-00023 | Studio 2
Mason cliffs, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00023 |
| browser-test-accommodation-00024 | Flat 86
Moss corners, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00024 |
| browser-test-accommodation-00025 | Flat 77u
Jean island, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00025 |
| browser-test-accommodation-00026 | Flat 01d
Hill walks, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00026 |
| browser-test-accommodation-00027 | Flat 69K
Hunter burg, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00027 |
| browser-test-accommodation-00028 | 53 Walsh divide, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00028 |
| browser-test-accommodation-00029 | 1 Warren dam, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00029 |
| browser-test-accommodation-00030 | 6 Luke avenue, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00030 |
| browser-test-accommodation-00031 | 78 Charlene cove, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00031 |
| browser-test-accommodation-00032 | Flat 7
Terry expressway, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00032 |
| browser-test-accommodation-00033 | Flat 1
Reece flat, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00033 |
| browser-test-accommodation-00034 | Flat 98
Pauline ports, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00034 |
| browser-test-accommodation-00035 | 189 Davison springs, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00035 |
| browser-test-accommodation-00036 | Flat 1
Shirley ridges, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00036 |
| browser-test-accommodation-00037 | 24 Ferguson pines, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00037 |
| browser-test-accommodation-00038 | 57 Gibson pine, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00038 |
| browser-test-accommodation-00039 | 8 Fowler trail, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00039 |
| browser-test-accommodation-00040 | 2 Hardy valleys, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00040 |
| browser-test-accommodation-00041 | 4 Victoria canyon, Isles of Scilly | Isles of Scilly | browser-test-ar-00040 |
| browser-test-accommodation-00042 | 09 Hill street, Isles of Scilly | Isles of Scilly |  |
| browser-test-accommodation-00043 | 09 Holt ford, Isles of Scilly | Isles of Scilly |  |
| browser-test-accommodation-00044 | 76 Helen spring, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00042 |
| browser-test-accommodation-00045 | 8 Callum branch, Hobbiton | Hobbiton (Browser test LTLA) | browser-test-ar-00043 |

### Groups (MvGroup)

| Id | Title |
| --- | --- |
| browser-test-group-00001 | Jade Smith |
| browser-test-group-00002 | Valerie Poole and 1 other |
| browser-test-group-00003 | Jeremy Hunt and 2 others |
| browser-test-group-00004 | Debra Bell |
| browser-test-group-00005 | Kirsty Hawkins and 1 other |
| browser-test-group-00006 | Edward Schofield and 2 others |
| browser-test-group-00007 | Dominic Curtis |
| browser-test-group-00008 | Dylan Kaur and 1 other |
| browser-test-group-00009 | Tom Byrne and 2 others |
| browser-test-group-00010 | Susan Robson |
| browser-test-group-00011 | Jonathan Greenwood and 1 other |
| browser-test-group-00012 | Yvonne Smith and 2 others |
| browser-test-group-00013 | Amber Ellis |
| browser-test-group-00014 | Ian Yates and 1 other |
| browser-test-group-00015 | Molly Mills and 2 others |
| browser-test-group-00016 | Valerie Jordan |
| browser-test-group-00017 | Martyn Field and 1 other |
| browser-test-group-00018 | Karen Brown and 2 others |
| browser-test-group-00019 | Diane Williams |
| browser-test-group-00020 | Charlene Hussain and 1 other |
| browser-test-group-00021 | Naomi Gibbs and 2 others |
| browser-test-group-00022 | Bernard Walton |
| browser-test-group-00023 | Yvonne Palmer and 1 other |
| browser-test-group-00024 | Leonard Arnold and 2 others |
| browser-test-group-00025 | Antony Davies |
| browser-test-group-00026 | Howard Parker and 1 other |
| browser-test-group-00027 | Rebecca Morgan and 2 others |
| browser-test-group-00028 | Diane Lowe |
| browser-test-group-00029 | Joan Daly and 1 other |
| browser-test-group-00030 | Helen Walker and 2 others |
| browser-test-group-00031 | Peter Lowe |
| browser-test-group-00032 | Albert Gibson and 1 other |
| browser-test-group-00033 | Harriet Thompson and 2 others |
| browser-test-group-00034 | Charlene Davies |
| browser-test-group-00035 | Joseph Thompson and 1 other |
| browser-test-group-00036 | Clive Evans and 2 others |
| browser-test-group-00037 | Stacey Harvey |
| browser-test-group-00038 | Gerard Simpson and 1 other |
| browser-test-group-00039 | Howard Johnson and 2 others |
| browser-test-group-00040 | Shane Adams |
| browser-test-group-00041 | Thomas Simpson |
| browser-test-group-00042 | Eileen Austin |
| browser-test-group-00043 | Abigail Richards |

### Visa applications

| Id | Applicant | Visa status | Unique application number |
| --- | --- | --- | --- |
| browser-test-visa-00001 | Jade Smith | Arrived | 1313-0000-00000001 |
| browser-test-visa-00002 | Valerie Poole | Arrived | 1313-0000-00000002 |
| browser-test-visa-00003 | Philip Berry | Issued | 1313-0000-00000002 |
| browser-test-visa-00004 | Dominic Hill | Confirmed | 1313-0000-00000003 |
| browser-test-visa-00005 | Abbie Barnett | Arrived | 1313-0000-00000003 |
| browser-test-visa-00006 | Jeremy Hunt | Pending | 1313-0000-00000003 |
| browser-test-visa-00007 | Debra Bell | Arrived | 1313-0000-00000004 |
| browser-test-visa-00008 | Reece Rice | Issued | 1313-0000-00000005 |
| browser-test-visa-00009 | Kirsty Hawkins | Refused | 1313-0000-00000005 |
| browser-test-visa-00010 | Barbara Reid | Arrived | 1313-0000-00000006 |
| browser-test-visa-00011 | Edward Schofield | Confirmed | 1313-0000-00000006 |
| browser-test-visa-00012 | Kerry Lowe | Withdrawn | 1313-0000-00000006 |
| browser-test-visa-00013 | Julie Cole | Pending | 1313-0000-00000008 |
| browser-test-visa-00014 | Dylan Kaur | Lapsed | 1313-0000-00000008 |
| browser-test-visa-00015 | Jake Edwards | Arrived | 1313-0000-00000009 |
| browser-test-visa-00016 | Tom Byrne | Arrived | 1313-0000-00000009 |
| browser-test-visa-00017 | Aimee Thomas | Arrived | 1313-0000-00000009 |
| browser-test-visa-00018 | Susan Robson | Issued | 1313-0000-00000010 |
| browser-test-visa-00019 | Lesley Williams | Confirmed | 1313-0000-00000011 |
| browser-test-visa-00020 | Jonathan Greenwood | Arrived | 1313-0000-00000011 |
| browser-test-visa-00021 | Yvonne Smith | Pending | 1313-0000-00000012 |
| browser-test-visa-00022 | Alexander Martin | Arrived | 1313-0000-00000012 |
| browser-test-visa-00023 | Kayleigh Reynolds | Issued | 1313-0000-00000012 |
| browser-test-visa-00024 | Megan Rowley | Arrived | 1313-0000-00000014 |
| browser-test-visa-00025 | Ian Yates | Confirmed | 1313-0000-00000014 |
| browser-test-visa-00026 | Neil Connolly | Withdrawn | 1313-0000-00000015 |
| browser-test-visa-00027 | Angela Patterson | Arrived | 1313-0000-00000015 |
| browser-test-visa-00028 | Molly Mills | Pending | 1313-0000-00000015 |
| browser-test-visa-00029 | Valerie Jordan | Lapsed | 1313-0000-00000016 |
| browser-test-visa-00030 | Martyn Field | Arrived | 1313-0000-00000017 |
| browser-test-visa-00031 | Kim Cooper | Arrived | 1313-0000-00000017 |
| browser-test-visa-00032 | Karen Brown | Arrived | 1313-0000-00000018 |
| browser-test-visa-00033 | Barry Harris | Issued | 1313-0000-00000018 |
| browser-test-visa-00034 | Barbara Smith | Confirmed | 1313-0000-00000018 |
| browser-test-visa-00035 | Diane Williams | Arrived | 1313-0000-00000019 |
| browser-test-visa-00036 | Rosemary Thomas | Pending | 1313-0000-00000020 |
| browser-test-visa-00037 | Charlene Hussain | Arrived | 1313-0000-00000020 |
| browser-test-visa-00038 | Ashleigh Kelly | Issued | 1313-0000-00000021 |
| browser-test-visa-00039 | Rhys Wood | Refused | 1313-0000-00000021 |
| browser-test-visa-00040 | Naomi Gibbs | Arrived | 1313-0000-00000021 |
| browser-test-visa-00041 | Bernard Walton | Confirmed | 1313-0000-00000022 |
| browser-test-visa-00042 | Yvonne Palmer | Withdrawn | 1313-0000-00000023 |
| browser-test-visa-00043 | Bernard Kerr | Arrived | 1313-0000-00000023 |
| browser-test-visa-00044 | Donald Butler | Pending | 1313-0000-00000024 |
| browser-test-visa-00045 | Georgia McDonald | Lapsed | 1313-0000-00000024 |
| browser-test-visa-00046 | Leonard Arnold | Arrived | 1313-0000-00000024 |
| browser-test-visa-00047 | Antony Davies | Arrived | 1313-0000-00000025 |
| browser-test-visa-00048 | Howard Parker | Arrived | 1313-0000-00000026 |
| browser-test-visa-00049 | Tina Farmer | Issued | 1313-0000-00000026 |
| browser-test-visa-00050 | Rebecca Morgan | Confirmed | 1313-0000-00000027 |
| browser-test-visa-00051 | Francesca Young | Arrived | 1313-0000-00000027 |
| browser-test-visa-00052 | Andrea West | Pending | 1313-0000-00000027 |
| browser-test-visa-00053 | Joan Daly | Issued | 1313-0000-00000029 |
| browser-test-visa-00054 | Glen Davies | Refused | 1313-0000-00000029 |
| browser-test-visa-00055 | Paul Parker | Arrived | 1313-0000-00000030 |
| browser-test-visa-00056 | Helen Walker | Confirmed | 1313-0000-00000030 |
| browser-test-visa-00057 | Fiona Taylor | Withdrawn | 1313-0000-00000030 |
| browser-test-visa-00058 | Albert Gibson | Pending | 1313-0000-00000032 |
| browser-test-visa-00059 | Wayne Turner | Lapsed | 1313-0000-00000032 |
| browser-test-visa-00060 | Harriet Thompson | Arrived | 1313-0000-00000033 |
| browser-test-visa-00061 | Samuel Bates | Arrived | 1313-0000-00000033 |
| browser-test-visa-00062 | Sally Watson | Arrived | 1313-0000-00000033 |
| browser-test-visa-00063 | Charlene Davies | Issued | 1313-0000-00000034 |
| browser-test-visa-00064 | Teresa Smith | Confirmed | 1313-0000-00000035 |
| browser-test-visa-00065 | Joseph Thompson | Arrived | 1313-0000-00000035 |
| browser-test-visa-00066 | Gregory Mitchell | Pending | 1313-0000-00000036 |
| browser-test-visa-00067 | Clive Evans | Arrived | 1313-0000-00000036 |
| browser-test-visa-00068 | Sheila Davis | Issued | 1313-0000-00000036 |
| browser-test-visa-00069 | Charlie Lewis | Arrived | 1313-0000-00000038 |
| browser-test-visa-00070 | Gerard Simpson | Confirmed | 1313-0000-00000038 |
| browser-test-visa-00071 | Howard Johnson | Withdrawn | 1313-0000-00000039 |
| browser-test-visa-00072 | Sarah Barrett | Arrived | 1313-0000-00000039 |
| browser-test-visa-00073 | Julia Evans | Pending | 1313-0000-00000039 |
| browser-test-visa-00074 | Shane Adams | Lapsed | 1313-0000-00000040 |
| browser-test-visa-00075 | Shane Adams | Pending | 1313-0000-00000041 |
| browser-test-visa-00076 | Thomas Simpson | Confirmed | 1313-0000-00000042 |
| browser-test-visa-00077 | Eileen Austin | Confirmed | 1313-0000-00000043 |
| browser-test-visa-00078 | Abigail Richards | Confirmed | 1313-0000-00000044 |

### Checks (DevCheckV2)

| Id | Type | Status | Failure reason | AR(s) |
| --- | --- | --- | --- | --- |
| browser-test-check-00001 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00003 |
| browser-test-check-00002 | Accommodation suitable | Passed |  | browser-test-ar-00004 |
| browser-test-check-00003 | Accommodation exists | Passed |  | browser-test-ar-00004 |
| browser-test-check-00004 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00004 |
| browser-test-check-00005 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00004 |
| browser-test-check-00006 | Uk Form Uploaded |  |  |  |
| browser-test-check-00007 | Ukr Form Uploaded |  |  |  |
| browser-test-check-00008 | DBS check and Sponsor suitable | Failed | NO_RESPONSE | browser-test-ar-00007 |
| browser-test-check-00009 | Accommodation suitable | Passed |  | browser-test-ar-00008 |
| browser-test-check-00010 | Accommodation exists | Passed |  | browser-test-ar-00008 |
| browser-test-check-00011 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00008 |
| browser-test-check-00012 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00008 |
| browser-test-check-00013 | Accommodation suitable | Passed |  | browser-test-ar-00011 |
| browser-test-check-00014 | Accommodation suitable | Passed |  | browser-test-ar-00012 |
| browser-test-check-00015 | Accommodation exists | Passed |  | browser-test-ar-00012 |
| browser-test-check-00016 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00012 |
| browser-test-check-00017 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00012 |
| browser-test-check-00018 | Uk Form Uploaded |  |  |  |
| browser-test-check-00019 | Ukr Form Uploaded |  |  |  |
| browser-test-check-00020 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00015 |
| browser-test-check-00021 | Accommodation suitable | Passed |  | browser-test-ar-00016 |
| browser-test-check-00022 | Accommodation exists | Passed |  | browser-test-ar-00016 |
| browser-test-check-00023 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00016 |
| browser-test-check-00024 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00016 |
| browser-test-check-00025 | Accommodation suitable | Passed |  | browser-test-ar-00020 |
| browser-test-check-00026 | Accommodation exists | Passed |  | browser-test-ar-00020 |
| browser-test-check-00027 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00020 |
| browser-test-check-00028 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00020 |
| browser-test-check-00029 | Accommodation suitable | Passed |  | browser-test-ar-00023 |
| browser-test-check-00030 | Accommodation suitable | Passed |  | browser-test-ar-00024 |
| browser-test-check-00031 | Accommodation exists | Passed |  | browser-test-ar-00024 |
| browser-test-check-00032 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00024 |
| browser-test-check-00033 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00024 |
| browser-test-check-00034 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00027 |
| browser-test-check-00035 | Uk Form Uploaded |  |  |  |
| browser-test-check-00036 | Ukr Form Uploaded |  |  |  |
| browser-test-check-00037 | Uk Form Uploaded |  |  |  |
| browser-test-check-00038 | Ukr Form Uploaded |  |  |  |
| browser-test-check-00039 | Accommodation suitable | Passed |  | browser-test-ar-00032 |
| browser-test-check-00040 | Accommodation exists | Passed |  | browser-test-ar-00032 |
| browser-test-check-00041 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00032 |
| browser-test-check-00042 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00032 |
| browser-test-check-00043 | Accommodation suitable | Passed |  | browser-test-ar-00035 |
| browser-test-check-00044 | Accommodation suitable | Passed |  | browser-test-ar-00036 |
| browser-test-check-00045 | Accommodation exists | Passed |  | browser-test-ar-00036 |
| browser-test-check-00046 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00036 |
| browser-test-check-00047 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00036 |
| browser-test-check-00048 | Uk Form Uploaded |  |  |  |
| browser-test-check-00049 | Ukr Form Uploaded |  |  |  |
| browser-test-check-00050 | Accommodation exists | Passed |  | browser-test-ar-00039 |
| browser-test-check-00051 | Accommodation suitable | Passed |  | browser-test-ar-00040 |
| browser-test-check-00052 | Accommodation exists | Passed |  | browser-test-ar-00040 |
| browser-test-check-00053 | DBS check and Sponsor suitable | Passed |  | browser-test-ar-00040 |
| browser-test-check-00054 | Guests have arrived in their accommodation | Passed |  | browser-test-ar-00040 |

### Safeguarding notifications

| Id | AR | Check |
| --- | --- | --- |
| 90c465bf-6f1c-4bbb-8701-de40988f19cb | browser-test-ar-00007 | browser-test-check-00008 |

### Reassignment requests

| Id | Outcome | Destination LA | AR |
| --- | --- | --- | --- |
| browser-test-rr-00001 | Rejected | Isles of Scilly | browser-test-ar-00039 |
| rr-18f74a82-5549-483a-ae3f-818715483340 | Accepted | Hobbiton (Browser test LTLA) | browser-test-ar-00041 |
| rr-ab5f413d-003f-4891-ac8c-e6dca38298d7 | Pending | Isles of Scilly | browser-test-ar-00016 |

### Visa information request records

| Id | Status | Visa application | Title |
| --- | --- | --- | --- |
| browser-test-vir-00001 | Awaiting LA | browser-test-visa-00001 | Visa information request for Jade Smith |
| browser-test-vir-00002 | Awaiting UKVI | browser-test-visa-00002 | Visa information request for Valerie Poole |
| browser-test-vir-00003 | Closed | browser-test-visa-00003 | Visa information request for Philip Berry |
