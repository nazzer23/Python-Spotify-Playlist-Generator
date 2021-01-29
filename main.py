import os
import json
import sys

import requests

from secrets import spotifyToken, spotifyUserID
from blacklists import genreWhitelist, artistBlacklist

class SpotifySuggestions:
    def __init__(self):
        print("Initialised.")
        self.spotifyGenres = []
        self.genres = []
        self.songURIs = []
        self.currentPlaylistItems = []

    def populate(self):
        self.fetchSpotifyGenreSeeds()

        self.fetchGenres()

        self.playlistID = self.checkPlaylist()

        # Fetch the items the playlists current songs
        self.fetchSongsFromPlaylist()
        print(f'Amount of songs in playlist before adding songs: {len(self.currentPlaylistItems)}')

        for genre in self.genres:
            print(f"Fetching songs from {genre}")
            self.fetchRecommended(genre)
            self.addSongsToPlaylist()

        print(f'Amount of songs in playlist before adding songs: {len(self.currentPlaylistItems)}')
        
    def addSongsToPlaylist(self):
        query = f'https://api.spotify.com/v1/playlists/{self.playlistID}/tracks'
        tempArr = [x for x in self.songURIs if x not in self.currentPlaylistItems]
        req_data = json.dumps(tempArr)
        response = requests.post(
            query,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotifyToken)
            }
        )
        self.currentPlaylistItems.extend(tempArr)
        self.songURIs = []

    def checkPlaylist(self):
        query = "https://api.spotify.com/v1/me/playlists"
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotifyToken)
            }
        )
        responseJson = response.json()

        playlists = responseJson["items"]
        
        playlistID = 0
        for playlist in playlists:
            if playlist["name"] == "Auto-Generated - Nazzer":
                playlistID = playlist["id"]

        if playlistID == 0:
            return self.createPlaylist()
        else:
            return playlistID

    def createPlaylist(self):
        query = f'https://api.spotify.com/v1/users/{spotifyUserID}/playlists'
        data = json.dumps({
            "name": "Auto-Generated - Nazzer",
            "description": "This playlist was automatically genereated by Nazzer's Spotify Script.",
            "public": False
        })
        response = requests.post(
            query,
            data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotifyToken)
            }
        )
        responseJson = response.json()
        self.playlistID = responseJson["id"]
        return self.playlistID

    def fetchRecommended(self, genre):
        query = "https://api.spotify.com/v1/recommendations"
        data = {
            "seed_genres": genre,
            "limit":100,
            "market":"GB"
        }
        response = requests.get(
            query,
            data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotifyToken)
            }
        )

        responseJson = response.json()
        for item in responseJson["tracks"]:
            if item["artists"][0]["name"] not in artistBlacklist:
                print(f'[{genre}]{item["artists"][0]["name"]} - {item["name"]} - {item["uri"]}')
                self.songURIs.append(item["uri"])

    def fetchSpotifyGenreSeeds(self):
        query = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotifyToken)
            }
        )
        responseJson = response.json()
        if "genres" in responseJson:
            self.spotifyGenres = responseJson["genres"]
        else:
            print(responseJson)
            sys.exit()
            return

    def fetchGenres(self):
        query = "https://api.spotify.com/v1/me/top/artists"
        data = {
            "limit":50,
            "time_range":"short_term"
        }
        response = requests.get(
            query,
            data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotifyToken)
            }
        )
        responseJson = response.json()

        if "items" in responseJson:
            for item in responseJson["items"]:
                self.genres.extend(item["genres"])
        else:
            print(responseJson)
            sys.exit()
            return

        self.frequentGenre = self.mostFrequentElement(self.genres)

        temp = []
        for genre in self.genres:
            temp.extend(genre.split(" "))
        temp.sort()
        self.genres = list(dict.fromkeys(temp))

        tempGenres = []

        # Compare to spotify genres
        for item in self.genres:
            if item in self.spotifyGenres:
                tempGenres.append(item)
        self.genres = tempGenres

        print(f"Genres before blacklist: {self.genres}")

        tempGenres = []
        for item in self.genres:
            if item in genreWhitelist:
                print(item)
                tempGenres.append(item)

        self.genres = (list(dict.fromkeys(tempGenres)))
        
        print(f'All Genres:{self.genres}')
        print(f'Most Frequent Genre: {self.frequentGenre}')

    def fetchSongsFromPlaylist(self):
        offset = 0
        end = False
        while not end:
            query = f'https://api.spotify.com/v1/playlists/{self.playlistID}/tracks?offset={offset}'
            response = requests.get(
                query,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {}".format(spotifyToken)
                }
            )
            playlistData = response.json()
            if len(playlistData["items"]) > 0:
                for playlistItems in playlistData["items"]:
                    track = playlistItems["track"]
                    self.currentPlaylistItems.append(track["uri"])
                offset = offset+100
            else:
                end = True
        

    def mostFrequentElement(self, List): 
        counter = 0
        num = List[0] 
        
        for i in List: 
            curr_frequency = List.count(i) 
            if(curr_frequency> counter): 
                counter = curr_frequency 
                num = i 
    
        return num 


if __name__ == '__main__':
    suggestions = SpotifySuggestions()
    suggestions.populate()
