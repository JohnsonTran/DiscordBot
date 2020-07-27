import discord
from discord.ext import commands
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.endpoints import scoreboard
from nba_api.stats.static import teams
from nba_api.stats.library.parameters import GameDate
import json
import numpy

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

options = Options()
options.add_argument("--headless")
browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)


class nba(commands.Cog):

    left_arrow_emoji = '\U00002B05\U0000FE0F'
    right_arrow_emoji = '\U000027A1\U0000FE0F'
    blue_circle_emoji = '\U0001F535'

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("nba is ready to go")

    # returns the games/scores of a given date
    @commands.command()
    async def scores(self, ctx, *, date=GameDate.default):
        # default date is the current date
        try:
            score = scoreboard.Scoreboard(game_date=date)
            result = await self.get_scores(score)
            if result == '':
                await ctx.send('No games were played that day')
            else:
                embed = discord.Embed(title=f"Scores for {date}", description=result)
                await ctx.send(embed=embed)
        except:
            await ctx.send('Invalid date format, make sure the format is "YYYY-MM-DD" or "MM-DD-YYYY"')

    # formats the output for scores
    async def get_scores(self, score):
        result = '```'
        line_score = score.line_score
        ls_df = line_score.get_data_frame()
        ls_df['PTS'] = ls_df['PTS'].fillna(0).astype(numpy.int64)
        game_header = score.game_header
        gh_df = game_header.get_data_frame()
        if not ls_df.empty:
            team_points = ls_df[['TEAM_ID', 'PTS']]
            for x in range(0, len(team_points), 2):
                try:
                    away_team = teams.find_team_name_by_id(ls_df['TEAM_ID'][x])['nickname']
                    home_team = teams.find_team_name_by_id(ls_df['TEAM_ID'][x + 1])['nickname']
                # handles case where teams are not in the list of current teams i.e. Team LeBron, West All-Stars
                except:
                    away_team = ls_df['TEAM_CITY_NAME'][x] + ' ' + ls_df['TEAM_ABBREVIATION'][x]
                    home_team = ls_df['TEAM_CITY_NAME'][x + 1] + ' ' + ls_df['TEAM_ABBREVIATION'][x+1]
                away_points = ls_df['PTS'][x]
                home_points = ls_df['PTS'][x + 1]
                away_win = ''
                home_win = ''
                if home_points > away_points:
                    home_win = '**'
                else:
                    away_win = '**'
                # result += f"{away_win}{away_team}  {away_points}{away_win} - {home_win}{home_points}  {home_team}{home_win} {gh_df['GAME_STATUS_TEXT'][x // 2]}\n"
                result += f"{away_team:<14} {int(away_points):>3}-{int(home_points):<3} {home_team:>14}   {gh_df['GAME_STATUS_TEXT'][x // 2]}\n"
        result += '```'
        return result

    # returns the player's information from the API
    async def get_player_info(self, ctx, player_name):
        from nba_api.stats.static import players

        player_dict = players.get_players()
        player_name = player_name.lower()
        player_info = [player for player in player_dict if (player['full_name'].lower() == player_name or
                                                            player['first_name'].lower() == player_name or
                                                            player['last_name'].lower() == player_name)]
        if len(player_name) == 0:
            await ctx.send('Please provide a player\'s name')
        elif len(player_info) == 1:
            return player_info[0]
        elif len(player_info) > 1:
            msg = f"Results for {player_name}:\n"
            for player in player_info:
                msg += f"{player['full_name']}\n"
            await ctx.send(msg)
        else:
            await ctx.send('Couldn\'t find the player.')
        return None

    # returns the careers stats of a given player
    @commands.command()
    async def pcareerstat(self, ctx, *, player_name=''):
        try:
            player_info = await self.get_player_info(ctx, player_name)
            player_id = player_info['id']
        except IndexError:
            # get_player_info handles name issues
            pass
        else:
            img_link = await self.get_player_image(player_id)
            career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
            career_tot = career_stats.career_totals_regular_season.get_data_frame()
            embed = discord.Embed(title=f"Career Stats for {player_info['full_name']}:\n")
            result = '```'
            for cat in range(3, len(career_tot.columns)):  # filters out the player, league, and team ID
                category = career_tot.columns[cat]
                result += f"{category}: {career_tot[category][0]}\n"
            result += '```'
            embed.description = result
            embed.set_thumbnail(url=img_link)
            await ctx.send(embed=embed)

    # returns the image of the player
    async def get_player_image(self, player_id):
        # tries to see if it is the local JSON file and gets it from the web if not
        with open('player_img.json') as f:
            images = json.load(f)
        if str(player_id) not in images:
            browser.get(f"https://stats.nba.com/player/{player_id}/")
            data = BeautifulSoup(browser.page_source, 'lxml')
            img_link = data.find(class_='player-img')['src']
            images[player_id] = [img_link]
            with open('player_img.json', 'w') as f:
                json.dump(images, f, indent=4)
        else:
            img_link = images[str(player_id)][0]
        return img_link

    # returns the careers stats of a given player
    @commands.command()
    async def pseasonstat(self, ctx, *data):
        # makes sure the input is in the correct format and separates the player name and the season
        processed_data = await self.process_season_input(data)
        try:
            player_name, season = processed_data[0], processed_data[1]
            season = str(season) + '-' + str(season + 1)[-2:]  # configure the season year to fit the API arguments
        except (IndexError, TypeError):
            await ctx.send('Please provide the player\'s name and season.')
        else:
            # checks if the user inputted a valid player
            try:
                player_info = await self.get_player_info(ctx, player_name)
                player_id = player_info['id']
                player_career_stats = playercareerstats.PlayerCareerStats(player_id=player_id)
            except IndexError:
                # get_player_info handles name issues
                pass
            else:
                # checks if the user inputted a valid season for the player
                try:
                    # sends the initial data
                    season_tot = player_career_stats.season_totals_regular_season.get_data_frame()
                    season_info = season_tot[season_tot['SEASON_ID'] == season]
                    toggle_per_game = False
                    index = 0
                    img_link = await self.get_player_image(player_id)
                    embed = await self.make_season_embed(player_info, season, toggle_per_game, index, img_link)
                except IndexError:
                    await ctx.send('The player did not play in that season')
                else:
                    msg = await ctx.send(embed=embed)
                    await msg.add_reaction(emoji=self.blue_circle_emoji)

                    # if the player played on more than one team for a season, the stats for each team is showcased in
                    # a carousel format for the user
                    if len(season_info.index) > 1:
                        await msg.add_reaction(emoji=self.left_arrow_emoji)
                        await msg.add_reaction(emoji=self.right_arrow_emoji)

                    check = lambda reaction, user: self.client.user != user
                    rows = list(season_info.index)

                    # keeps responding to input until the message times out
                    while True:
                        res = await self.client.wait_for('reaction_add', timeout=30, check=check)
                        if res:
                            cache_msg = res[0].message
                            # checks the id so it can update the correct message
                            if cache_msg.id == msg.id:
                                emoji = str(res[0])
                                change = True
                                if emoji == self.left_arrow_emoji:
                                    index = (index - 1) % (len(rows) - 1)
                                elif emoji == self.right_arrow_emoji:
                                    index = (index + 1) % (len(rows) - 1)
                                elif emoji == self.blue_circle_emoji:
                                    toggle_per_game = not toggle_per_game
                                else:
                                    change = False

                                # only edit the embed when the user reacts with an appropriate emoji
                                if change:
                                    embed = await self.make_season_embed(player_info, season, toggle_per_game, index, img_link)
                                    await cache_msg.edit(embed=embed)

    # helper method to process the input for pseasonstat
    async def process_season_input(self, data):
        # tests if the last argument is a season
        try:
            season = int(data[-1])
        except (IndexError, ValueError):
            return None
        # makes sure there is a name and season
        if len(data) == 2:
            return data[0], season
        elif len(data) == 3:
            return data[0] + ' ' + data[1], season
        else:
            return None

    # helper method to get the season stats of a player and create an embed
    async def make_season_embed(self, player_info, season, toggle_per_game, index, img_link):
        player_id = player_info['id']
        player_career_stats = playercareerstats.PlayerCareerStats(player_id=player_id,
                                                                  per_mode36='PerGame' if toggle_per_game else 'Totals')
        season_tot = player_career_stats.season_totals_regular_season.get_data_frame()
        season_info = season_tot[season_tot['SEASON_ID'] == season]
        categories = season_info.columns
        stats = season_info.values
        embed = discord.Embed(title=f"{season} Season Stats for {player_info['full_name']}:\n")
        team_id = stats[index][categories.get_loc('TEAM_ID')]  # gets the player's team for the given season
        player_team = teams.find_team_name_by_id(team_id)
        result = f"```TEAM: {player_team['full_name']}\n"
        for cat in range(5, len(categories)):  # filters out the player, league, and team ID
            result += f"{categories[cat]}: {stats[index][cat]}\n"
        result += '```'
        embed.description = result
        embed.set_thumbnail(url=img_link)
        return embed

    # returns the league standings
    @commands.command()
    async def standings(self, ctx):
        from nba_api.stats.endpoints import leaguestandings
        standings = leaguestandings.LeagueStandings()
        stand_df = standings.get_data_frames()[0]
        east_stand = stand_df[stand_df['Conference'] == 'East']
        west_stand = stand_df[stand_df['Conference'] == 'West']

        embed = discord.Embed(title='Current Standings:')

        east_result = ''
        for i, row in enumerate(east_stand.itertuples(), 1):
            east_result += f"`{i:<3} {teams.find_team_name_by_id(row.TeamID)['full_name']:23} {row.Record:5}`\n"
        embed.add_field(name='Eastern Conference', value=east_result, inline=True)
        west_result = ''
        for i, row in enumerate(west_stand.itertuples(), 1):
            west_result += f"`{i:<3} {teams.find_team_name_by_id(row.TeamID)['full_name']:23} {row.Record:5}`\n"
        embed.add_field(name='Western Conference', value=west_result, inline=True)
        await ctx.send(embed=embed)

    # returns the league leaders for a given statistic
    @commands.command()
    async def leagueleaders(self, ctx, stat=''):
        from nba_api.stats.endpoints import homepageleaders
        from nba_api.stats.library.parameters import PlayerOrTeam

        stat_cat = await self.get_stat_cat(stat.upper())
        if stat_cat is None:
            await ctx.send('Please input a valid category. The categories are: PTS, AST, REB, and BLK')
        else:
            leaders = homepageleaders.HomePageLeaders(player_or_team=PlayerOrTeam.player, stat_category=stat_cat)
            leaders_df = leaders.get_data_frames()[0]
            embed = discord.Embed(title=f"League Leaders for {stat.upper()} Per Game")
            result = f"`{'Rank':<4}  {'Name':23} {stat.upper():>5}`\n"
            for index, row in leaders_df.iterrows():
                result += f"`{row.RANK:<4}  {row.PLAYER:23} {row[stat.upper()]:5}`\n"
            embed.description = result
            await ctx.send(embed=embed)

    # returns the API category parameter based on string input
    async def get_stat_cat(self, category):
        from nba_api.stats.library.parameters import StatCategory

        return {
            'PTS': StatCategory.points,
            'AST': StatCategory.assists,
            'REB': StatCategory.rebounds,
            'BLK': StatCategory.defense
        }.get(category, None)

    # adds a player to a user's favorites list
    @commands.command()
    async def fav(self, ctx, *, player_name=''):
        try:
            player_info = await self.get_player_info(ctx, player_name)
            player_name = player_info['full_name']
            user_id = str(ctx.author.id)
            with open('user_favorites.json') as f:
                favorites = json.load(f)
            if not favorites or user_id not in favorites:
                favorites[user_id] = [player_name]
            else:
                fav_list = list(favorites[user_id])
                if player_name not in fav_list:
                    fav_list.append(player_name)
                    favorites[user_id] = fav_list
                    await ctx.send(f"{player_name} has been added to your favorites list.")
                else:
                    await ctx.send(f"{player_name} is already on your favorites list.")
            with open('user_favorites.json', 'w') as f:
                json.dump(favorites, f, indent=4)
        except IndexError:
            # get_player_info handles name issues
            pass

    # returns the user's favorites list
    @commands.command()
    async def favlist(self, ctx):
        user_id = str(ctx.author.id)
        with open('user_favorites.json') as f:
            favorites = json.load(f)
        if not favorites or user_id not in favorites:
            await ctx.send('You don\'t anyone on your favorites list')
        else:
            fav_list = favorites[user_id]
            embed = discord.Embed(title=f"{ctx.author.display_name}\'s Favorites List")
            result = ''
            for player in fav_list:
                result += f"**{player}**\n"
            embed.description = result
            await ctx.send(embed=embed)

    # removes a player from the user's favorites list
    @commands.command()
    async def favremove(self, ctx, *, player_name=''):
        try:
            player_info = await self.get_player_info(ctx, player_name)
            player_name = player_info['full_name']
            user_id = str(ctx.author.id)
            with open('user_favorites.json') as f:
                favorites = json.load(f)
            if not favorites or user_id not in favorites:
                favorites[user_id] = [player_name]
            else:
                fav_list = set(favorites[user_id])
                fav_list.remove(player_name)
                favorites[user_id] = list(fav_list)
            with open('user_favorites.json', 'w') as f:
                json.dump(favorites, f, indent=4)
            await ctx.send(f"{player_name} has been removed from your favorites list.")
        except IndexError:
            # get_player_info handles name issues
            pass


def setup(client):
    client.add_cog(nba(client))
