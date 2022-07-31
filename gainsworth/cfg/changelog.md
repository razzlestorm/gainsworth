# Change Log

## 0.2.5

Released on July 31, 2022.

### Added

* g!remove_me_please command will now delete ALL of a user's data.
* Gainsworth will now automatically remove your data if you don't interact with it for one year.
* If you'd like Gainsworth to keep your data saved until its end-of-life, you can opt-in to have your data stored with the g!save_my_data command.


## 0.2.4

Released on June 1, 2022.

### Changed

* Allow users to filter by day, as well as ints (for number of days)


## 0.2.3

Released on May 1, 2022.

### Added

* Added Changelog to announce changes to all users!
* Gainsworth config for tracking various info.


## 0.2.2

Released on April 1, 2022.

### Changed

* .lower() checks to arguments 
* accept all cases


## 0.2.1

Released on March 5, 2022.

### Added

* user_id column to DB, NEW primary key

### Changed

* Filter activities by time


## 0.2.0

Released on February 7, 2022.

### New Highlights

* Histogram option added to see_gains
* Various graphing bugfixes
* Time filters for list_gains

### Added

* You can now filter the list_gains function on time! Try `g!help list_gains` to see examples.

### Changed

* BREAKING: All command names with 'exercise' replaced with 'activity'.


## 0.1.3

Released on January 16, 2022.

### Changed

* Better error handling added to add_gains
* Add better number handling in names


## 0.1.2

Released on January 1, 2022.

### Changed

* Added histogram option to see_gains


## 0.1.1

Released on December 10, 2021.

### Changed

* add_gains function refactored to allow for args in pairs.


## 0.1.0

Released on December 5, 2021.

### Added

* First version of the Python project:
	- Documentation
	- Code of Conduct
	- Contributing guidelines
	- License
	- Manifest.in
	- README
	- Requirements.txt
	- Setup configuration
* DB Commands/CRUD functions
* Graphing function with see_gains

### Removed

### Changed

